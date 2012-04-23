# Copyright (C) 2012 by Tracelytics, Inc.
# All rights reserved.

from oboe_ext import *

import inspect
import sys
import types
import traceback as tb

# defaultdict not implemented before 2.5
from backport import defaultdict

__version__ = '0.4.8'
__all__ = ['config', 'Context', 'UdpReporter', 'Event']

# configuration
config = dict()
config['tracing_mode'] = 'through'
config['reporter_host'] = '127.0.0.1'
config['reporter_port'] = 7831

config['inst_enabled'] = defaultdict(lambda: True)

Context.init()

reporter_instance = None

try:
    import cStringIO, cProfile, pstats
    found_cprofile = True
except ImportError:
    found_cprofile = False

def _str_backtrace(backtrace=None):
    if backtrace:
        return "".join(tb.format_tb(backtrace))
    else:
        return "".join(tb.format_stack()[:-1])

def log(cls, layer, label, backtrace=False, **kwargs):
    """Report an individual tracing event.

        layer: layer name, None for "same as current"

        label: label of event

        backtrace: gather a backtrace?

        kwargs: extra key/value pairs to add to event

    """
    if not Context.isValid(): return
    evt = Context.createEvent()
    evt.addInfo('Layer', layer)
    evt.addInfo('Label', label)
    if backtrace:
        evt.addInfo('Backtrace', _str_backtrace())

    for k, v in kwargs.items():
        evt.addInfo(str(k), str(v))

    rep = reporter()
    return rep.sendReport(evt)


def log_error(cls, exception=None, err_class=None, err_msg=None, backtrace=True):
    """Report an error from python exception or from specified message.

        requires either exception to be set to a python Exception object,
        or err_class and err_msg to be set to strings describing the
        class of the error and the message for this particular instance of it.

    """
    if not Context.isValid(): return
    if not exception and not err_class: return
    evt = Context.createEvent()
    evt.addInfo('Label', 'error')
    if backtrace:
        _, _, tb = sys.exc_info()
        evt.addInfo('Backtrace', _str_backtrace(tb))

    if exception:
        evt.addInfo('ErrorClass', exception.__class__.__name__)
        evt.addInfo('ErrorMsg', str(exception))
    else:
        evt.addInfo('ErrorClass', err_class)
        evt.addInfo('ErrorMsg', err_msg)

    rep = reporter()
    return rep.sendReport(evt)

def log_exception(cls, msg=None, exc_info=None):
    """Report the message with exception information included. This should only
    be called from an exception handler, unless exc_info is provided."""

    if not Context.isValid():
        return

    typ, val, tb = exc_info or sys.exc_info()
    if msg is None:
        msg = str(val)

    evt = Context.createEvent()
    evt.addInfo('Label', 'error')
    evt.addInfo('Backtrace', _str_backtrace(tb))
    evt.addInfo('ErrorClass', typ.__name__)
    evt.addInfo('ErrorMsg', msg)

    return reporter().sendReport(evt)


def _function_signature(func):
    name = func.__name__
    (args, varargs, keywords, defaults) = inspect.getargspec(func)
    argstrings = []
    if defaults:
        first = len(args)-len(defaults)
        argstrings = args[:first]
        for i in range(first, len(args)):
            d = defaults[i-first]
            if isinstance(d, str):
                d = "'"+d+"'"
            else:
                d = str(d)
            argstrings.append(args[i]+'='+d)
    else:
        argstrings = args
    if varargs:
        argstrings.append('*'+varargs)
    if keywords:
        argstrings.append('**'+keywords)
    return name+'('+', '.join(argstrings)+')'


class profile_block(object):
    """A context manager for oboe profiling a block of code with Tracelytics Oboe.

          profile_name: the profile name to use when reporting.
          this should be unique to the profiled method.

          store_backtrace: whether to capture a backtrace or not (False)

          profile: profile this function with cProfile and report the result

          Reports an error event between entry and exit if an
          exception is thrown, then reraises.
    """
    def __init__(self, profile_name, profile=False, store_backtrace=False):
        self.profile_name = profile_name
        self.use_cprofile = profile
        self.backtrace = store_backtrace
        self.p = None # possible cProfile.Profile() instance

    def __enter__(self):
        if not Context.isValid():
            return

        # build entry event
        entry_kvs = { 'Language' : 'python',
                      'ProfileName' : self.profile_name,
                        # XXX We can definitely figure out a way to make these
                        # both available and fast.  For now, this is ok.
                      'File': '',
                      'LineNumber': 0,
                      'Module': '',
                      'FunctionName': '',
                      'Signature': ''}
        if self.backtrace:
            entry_kvs['Backtrace'] = _str_backtrace()
        Context.log(None, 'profile_entry', **entry_kvs)

        # begin profiling
        if self.use_cprofile and found_cprofile:
            self.p = cProfile.Profile()
            self.p.enable(subcalls=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not Context.isValid():
            return

        # end profiling
        stats = None
        if self.use_cprofile and found_cprofile and self.p:
            sio = cStringIO.StringIO()
            s = pstats.Stats(self.p, stream=sio)
            s.sort_stats('time')
            s.print_stats(15)
            stats = sio.getvalue()
            sio.close()

        # exception?
        if exc_type:
            Context.log(None, 'error', ErrorClass=exc_type.__name__, ErrorMsg=str(exc_val), backtrace=_str_backtrace(exc_tb))

        # build exit event
        exit_kvs = {}
        if self.use_cprofile and stats:
            exit_kvs['ProfileStats'] = stats
        exit_kvs['Language'] = 'python'
        exit_kvs['ProfileName'] = self.profile_name

        Context.log(None, 'profile_exit', **exit_kvs)

def profile_function(cls, profile_name,
                   store_args=False, store_return=False, store_backtrace=False, profile=False, callback=None, **entry_kvs):
    """Wrap a method for tracing and profiling with the Tracelytics Oboe library.

          profile_name: the profile name to use when reporting.
          this should be unique to the profiled method.

          store_return: report the return value of this function

          store_args: report the arguments to this function

          store_backtrace: whether to capture a backtrace or not (False)

          profile: profile this function with cProfile and report the result

          callback: if set, calls this function after the wrapped
          function returns, which examines the function, arguments,
          and return value, and may add more K/V pairs to the
          dictionary to be reported

          Reports an error event between entry and exit if an
          exception is thrown, then reraises.

    """
    from decorator import decorator

    # run-time event-reporting function, called at each invocation of func(f_args, f_kwargs)
    def _profile_wrapper(func, *f_args, **f_kwargs):
        if not Context.isValid():            # tracing not enabled?
            return func(*f_args, **f_kwargs) # pass through to func right away
        if store_args:
            entry_kvs.update({'Args': f_args, 'kwargs': f_kwargs })

        if 'im_class' in dir(func):          # is func an instance method?
            entry_kvs['Class'] = func.im_class.__name__


        try:
            # get filename, line number, etc, and cache in wrapped function to avoid overhead
            if not hasattr(func, '_oboe_file'):
                setattr(func, '_oboe_file', inspect.getsourcefile(func))
            if not hasattr(func, '_oboe_line_number'):
                setattr(func, '_oboe_line_number', inspect.getsourcelines(func)[1])
            if not hasattr(func, '_oboe_module'):
                setattr(func, '_oboe_module', inspect.getmodule(func).__name__)
            if not hasattr(func, '_oboe_signature'):
                setattr(func, '_oboe_signature', _function_signature(func))
        except Exception, e:
            entry_kvs['_OboeError'] = 'Error getting function signature data: %s' % str(e)


        # prepare data for reporting oboe event
        entry_kvs.update({'Language': 'python',
                       'ProfileName': profile_name,
                       'File': getattr(func, '_oboe_file', 'None'),
                       'LineNumber': getattr(func, '_oboe_line_number', 'None'),
                       'Module': getattr(func, '_oboe_module', 'None'),
                       'FunctionName': func.__name__,
                       'Signature': getattr(func, '_oboe_signature', 'None')})

        if store_backtrace:
            entry_kvs['Backtrace'] = _str_backtrace()

        # log entry event for this profiled function
        Context.log(None, 'profile_entry', **entry_kvs)

        res = None   # return value of wrapped function
        stats = None # cProfile statistics, if enabled
        try:
            if profile and found_cprofile: # use cProfile?
                p = cProfile.Profile()
                res = p.runcall(func, *f_args, **f_kwargs) # call func via cProfile
                sio = cStringIO.StringIO()
                s = pstats.Stats(p, stream=sio)
                s.sort_stats('time')
                s.print_stats(15)
                stats = sio.getvalue()
                sio.close()
            else: # don't use cProfile, call func directly
                res = func(*f_args, **f_kwargs)
        except Exception, e:
            # log exception and re-raise
            Context.log(None, 'error', ErrorClass=e.__class__.__name__, ErrorMsg=str(e))
            raise
        finally:
            # prepare data for reporting exit event
            exit_kvs = {}

            # call the callback function, if set, and merge its return
            # values with the exit event's reporting data
            if callback and callable(callback):
                cb_kvs = callback(func, f_args, f_kwargs, res)
                if cb_kvs:
                    exit_kvs.update(cb_kvs)

            # (optionally) report return value
            if store_return:
                exit_kvs['ReturnValue'] = res

            # (optionally) report profiler results
            if profile and stats:
                exit_kvs['Profile'] = stats

            exit_kvs['Language'] = 'python'
            exit_kvs['ProfileName'] = profile_name

            # log exit event
            Context.log(None, 'profile_exit', **exit_kvs)

        return res # return output of func(*f_args, **f_kwargs)

    _profile_wrapper._oboe_wrapped = True      # mark our wrapper for protection below

    # instrumentation helper decorator, called to add wrapper at "decorate" time
    def decorate_with_profile_function(f):
        if getattr(f, '_oboe_wrapped', False): # has this function already been wrapped?
            return f                           # then pass through
        return decorator(_profile_wrapper, f)  # otherwise wrap function f with wrapper

    # return decorator function with arguments to profile_function() baked in
    return decorate_with_profile_function

def log_method(cls, layer='Python',
               store_return=False, store_args=False, callback=None, profile=False, **entry_kvs):
    """Wrap a method for tracing with the Tracelytics Oboe library.
        as opposed to profile_function, this decorator gives the method its own layer

          layer: the layer to use when reporting

          store_return: report the return value

          store_args: report the arguments to this function

          callback: if set, calls this function after the wrapped
          function returns, which examines the function, arguments,
          and return value, and may add more K/V pairs to the
          dictionary to be reported

          Reports an error event between entry and exit if an
          exception is thrown, then reraises.

    """
    from decorator import decorator

    # run-time event-reporting function, called at each invocation of func(f_args, f_kwargs)
    def _log_method_wrapper(func, *f_args, **f_kwargs):
        if not Context.isValid():            # tracing not enabled?
            return func(*f_args, **f_kwargs) # pass through to func right away
        if store_args:
            entry_kvs.update( {'args' : f_args, 'kwargs': f_kwargs} )

        # log entry event
        Context.log(layer, 'entry', **entry_kvs)

        res = None   # return value of wrapped function
        stats = None # cProfile statistics, if enabled
        try:
            if profile and found_cprofile: # use cProfile?
                p = cProfile.Profile()
                res = p.runcall(func, *f_args, **f_kwargs) # call func via cProfile
                sio = cStringIO.StringIO()
                s = pstats.Stats(p, stream=sio)
                s.sort_stats('time')
                s.print_stats(15)
                stats = sio.getvalue()
                sio.close()
            else: # don't use cProfile, call func directly
                res = func(*f_args, **f_kwargs)
        except Exception, e:
            # log exception and re-raise
            Context.log(layer, 'error', ErrorClass=e.__class__.__name__, Message=str(e))
            raise
        finally:
            # prepare data for reporting exit event
            exit_kvs = {}

            # call the callback function, if set, and merge its return
            # values with the exit event's reporting data
            if callback and callable(callback):
                cb_ret = callback(func, f_args, f_kwargs, res)
                if cb_ret:
                    exit_kvs.update(cb_ret)

            # (optionally) report return value
            if store_return:
                exit_kvs['ReturnValue'] = str(res)

            # (optionally) report profiler results
            if profile and stats:
                exit_kvs['Profile'] = stats

            # log exit event
            Context.log(layer, 'exit', **exit_kvs)

        return res # return output of func(*f_args, **f_kwargs)

    _log_method_wrapper._oboe_wrapped = True     # mark our wrapper for protection below

    # instrumentation helper decorator, called to add wrapper at "decorate" time
    def decorate_with_log_method(f):
        if getattr(f, '_oboe_wrapped', False):   # has this function already been wrapped?
            return f                             # then pass through
        return decorator(_log_method_wrapper, f) # otherwise wrap function f with wrapper

    # return decorator function with arguments to log_method() baked in
    return decorate_with_log_method

def reporter():
    global reporter_instance

    if not reporter_instance:
        reporter_instance = UdpReporter(config['reporter_host'], str(config['reporter_port']))

    return reporter_instance

def _Event_addInfo_safe(func):
    def wrapped(*args, **kw):
        try: # call SWIG-generated Event.addInfo (from oboe_ext.py)
            return func(*args, **kw)
        except NotImplementedError, e: # unrecognized type passed to addInfo SWIG binding
            # args: [self, KeyName, Value]
            if len(args) == 3 and isinstance(args[1], basestring):
                # report this error
                func(args[0], '_Warning', 'Bad type for %s: %s' % (args[1], type(args[2])))
                # last resort: coerce type to string
                if hasattr(args[2], '__str__'):
                    return func(args[0], args[1], str(args[2]))
                elif hasattr(args[2], '__repr__'):
                    return func(args[0], args[1], repr(args[2]))
    return wrapped

setattr(Event, 'addInfo', _Event_addInfo_safe(getattr(Event, 'addInfo')))
setattr(Context, log.__name__, types.MethodType(log, Context))
setattr(Context, log_error.__name__, types.MethodType(log_error, Context))
setattr(Context, log_exception.__name__, types.MethodType(log_exception, Context))
setattr(Context, log_method.__name__, types.MethodType(log_method, Context))
setattr(Context, profile_function.__name__, types.MethodType(profile_function, Context))
setattr(Context, profile_block.__name__, profile_block)

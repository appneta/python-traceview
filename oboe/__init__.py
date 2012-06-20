""" Tracelytics instrumentation API for Python.

Copyright (C) 2012 by Tracelytics, Inc.
All rights reserved.
"""
from oboe_ext import Context, Event, UdpReporter

import inspect
import random
import sys
import types
import traceback

# defaultdict not implemented before 2.5
from backport import defaultdict

from decorator import decorator

__version__ = '0.5.1'
__all__ = ['config', 'Context', 'UdpReporter', 'Event']

# configuration defaults
config = dict()
config['tracing_mode'] = 'through'      # always, through, never
config['sample_rate'] = 0.3             # out of 1.0
config['reporter_host'] = '127.0.0.1'   # you probably don't want to change the
config['reporter_port'] = 7831          # last two options

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
        return "".join(traceback.format_tb(backtrace))
    else:
        return "".join(traceback.format_stack()[:-1])

def log(cls, layer, label, backtrace=False, **kwargs):
    """Report an individual tracing event.

        layer: layer name, None for "same as current"

        label: label of event

        backtrace: gather a backtrace?

        kwargs: extra key/value pairs to add to event

    """
    if not Context.isValid():
        return
    evt = Context.createEvent()
    if backtrace:
        kwargs['Backtrace'] = _str_backtrace()

    _log_event(evt, layer, label, kvs=kwargs)

def log_error(cls, err_class, err_msg, store_backtrace=True, backtrace=None):
    """Report a custom error.

    This is for logging errors that are not associated with python exceptions --
    framework 404s, missing data, etc.

    Arguments:
        `err_class` - The class of error, e.g., the name of an exception class.
        `err_msg` - The full description of the error.
        `store_backtrace` [optional] - Whether to send a backtrace. Defaults to True.
        `backtrace` [optional] - The backtrace to report this error on. Defaults to the caller.
    """
    if not Context.isValid():
        return
    evt = Context.createEvent()
    evt.addInfo('Label', 'error')
    if store_backtrace:
        evt.addInfo('Backtrace', _str_backtrace(backtrace))

    evt.addInfo('ErrorClass', err_class)
    evt.addInfo('ErrorMsg', err_msg)

    rep = reporter()
    return rep.sendReport(evt)

def log_exception(cls, msg=None, store_backtrace=True):
    """Report the message with exception information included. This should only
    be called from an exception handler, unless exc_info is provided."""

    if not Context.isValid():
        return

    typ, val, tb = sys.exc_info()
    if typ is None:
        raise Exception('log_exception should only be called from an exception context (e.g., except: block)')
    if msg is None:
        msg = str(val)

    evt = Context.createEvent()
    evt.addInfo('Label', 'error')
    evt.addInfo('Backtrace', _str_backtrace(tb))
    evt.addInfo('ErrorClass', typ.__name__)
    evt.addInfo('ErrorMsg', msg)

    return reporter().sendReport(evt)

def trace(cls, layer='Python', xtr_hdr=None, kvs=None):
    """ Decorator to begin a new trace on a block of code.  Takes
        into account oboe.config['tracing_mode'] as well as
        oboe.config['sample_rate'], so may not always start a trace.

        layer: layer name to report as
        xtr_hdr: optional, incoming x-trace header if available
        kvs: optional, dictionary of additional key/value pairs to report
    """

    def _trace_wrapper(func, *f_args, **f_kwargs):
        _start_trace(layer, xtr_hdr, kvs)
        try:
            res = func(*f_args, **f_kwargs)
        except Exception:
            # log exception and re-raise
            Context.log_exception()
            raise
        finally:
            _end_trace(layer)

        return res # return output of func(*f_args, **f_kwargs)

    _trace_wrapper._oboe_wrapped = True     # mark our wrapper for protection below

    # instrumentation helper decorator, called to add wrapper at "decorate" time
    def decorate_with_trace(f):
        if getattr(f, '_oboe_wrapped', False):   # has this function already been wrapped?
            return f                             # then pass through
        return decorator(_trace_wrapper, f)      # otherwise wrap function f with wrapper

    return decorate_with_trace

def _log_event(evt, layer, label, kvs=None):
    """ Reports an event, attaching given layer, label, and kvs. """
    evt.addInfo('Layer', layer)
    evt.addInfo('Label', label)

    if kvs != None:
        for k, v in kvs.items():
            evt.addInfo(str(k), str(v))

    rep = reporter()
    return rep.sendReport(evt)

def _start_trace(layer, xtr_hdr=None, kvs=None):
    """ Begin a new trace.  Takes into account oboe.config['tracing_mode'] and
        oboe.config['sample_rate'], so may not always start a trace. """

    tracing_mode = config.get('tracing_mode')
    sample_rate = config.get('sample_rate')

    if not Context.isValid() and xtr_hdr and tracing_mode in ['always', 'through']:
        Context.fromString(xtr_hdr)

    if not Context.isValid() and tracing_mode == 'always' and random.random() < sample_rate:
        evt = Context.startTrace()
    elif Context.isValid() and tracing_mode != 'never':
        evt = Context.createEvent()

    if not Context.isValid():
        return
    _log_event(evt, layer, 'entry', kvs)

def _end_trace(layer, kvs=None):
    """ Marks the end of a trace.  Clears oboe.Context to reset tracing state. """
    if not Context.isValid():
        return
    evt = Context.createEvent()
    _log_event(evt, layer, 'exit', kvs)
    Context.clear()

def _function_signature(func):
    """Returns a string representation of the function signature of the given func."""
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
            Context.log(None, 'error', ErrorClass=exc_type.__name__, ErrorMsg=str(exc_val),
                        backtrace=_str_backtrace(exc_tb))

        # build exit event
        exit_kvs = {}
        if self.use_cprofile and stats:
            exit_kvs['ProfileStats'] = stats
        exit_kvs['Language'] = 'python'
        exit_kvs['ProfileName'] = self.profile_name

        Context.log(None, 'profile_exit', **exit_kvs)

def profile_function(cls, profile_name, store_args=False, store_return=False, store_backtrace=False,
                     profile=False, callback=None, **entry_kvs):
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
    # run-time event-reporting function, called at each invocation of func(f_args, f_kwargs)
    def _profile_wrapper(func, *f_args, **f_kwargs):
        if not Context.isValid():            # tracing not enabled?
            return func(*f_args, **f_kwargs) # pass through to func right away
        if store_args:
            entry_kvs.update({'Args': f_args, 'kwargs': f_kwargs })

        if 'im_class' in dir(func):          # is func an instance method?
            entry_kvs['Class'] = func.im_class.__name__

        # get filename, line number, etc, and cache in wrapped function to avoid overhead
        try:
            if not hasattr(func, '_oboe_file'):
                setattr(func, '_oboe_file', inspect.getsourcefile(func))
        except Exception, e:
            setattr(func, '_oboe_file', None)

        try:
            if not hasattr(func, '_oboe_line_number'):
                setattr(func, '_oboe_line_number', inspect.getsourcelines(func)[1])
        except Exception, e:
            setattr(func, '_oboe_line_number', None)

        try:
            if not hasattr(func, '_oboe_module'):
                setattr(func, '_oboe_module', inspect.getmodule(func).__name__)
        except Exception, e:
            setattr(func, '_oboe_module', None)

        try:
            if not hasattr(func, '_oboe_signature'):
                setattr(func, '_oboe_signature', _function_signature(func))
        except Exception, e:
            setattr(func, '_oboe_signature', None)

        # prepare data for reporting oboe event
        entry_kvs.update({'Language': 'python',
                       'ProfileName': profile_name,
                       'File': getattr(func, '_oboe_file'),
                       'LineNumber': getattr(func, '_oboe_line_number'),
                       'Module': getattr(func, '_oboe_module'),
                       'FunctionName': getattr(func, '__name__'),
                       'Signature': getattr(func, '_oboe_signature')})

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
        if hasattr(f, 'im_func'):              # Is this a bound method of an object
            f = f.im_func                      # then wrap the unbound method
        return decorator(_profile_wrapper, f)  # otherwise wrap function f with wrapper

    # return decorator function with arguments to profile_function() baked in
    return decorate_with_profile_function

def log_method(cls, layer='Python', store_return=False, store_args=False,
               before_callback=None, callback=None, profile=False, **entry_kvs):
    """Wrap a method for tracing with the Tracelytics Oboe library.
        as opposed to profile_function, this decorator gives the method its own layer

          layer: the layer to use when reporting

          store_return: report the return value

          store_args: report the arguments to this function

          before_callback: if set, calls this function before the wrapped
          function is called. This function can change the args and kwargs, and
          can return K/V pairs to be reported in the entry event.

          callback: if set, calls this function after the wrapped
          function returns, which examines the function, arguments,
          and return value, and may add more K/V pairs to the
          dictionary to be reported

          Reports an error event between entry and exit if an
          exception is thrown, then reraises.

    """
    # run-time event-reporting function, called at each invocation of func(f_args, f_kwargs)
    def _log_method_wrapper(func, *f_args, **f_kwargs):
        if not Context.isValid():            # tracing not enabled?
            return func(*f_args, **f_kwargs) # pass through to func right away
        if store_args:
            entry_kvs.update( {'args' : f_args, 'kwargs': f_kwargs} )
        if before_callback:
            before_res = before_callback(func, f_args, f_kwargs)
            if before_res:
                f_args, f_kwargs, extra_entry_kvs = before_res
                entry_kvs.update(extra_entry_kvs)

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
        if hasattr(f, 'im_func'):                # Is this a bound method of an object
            f = f.im_func                        # then wrap the unbound method
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
        except NotImplementedError: # unrecognized type passed to addInfo SWIG binding
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
setattr(Context, trace.__name__, types.MethodType(trace, Context))
setattr(Context, profile_function.__name__, types.MethodType(profile_function, Context))
setattr(Context, profile_block.__name__, profile_block)

from oboe_ext import *

import types
import traceback as tb
import inspect

__all__ = ['config', 'Context', 'UdpReporter', 'Event']

config = dict()
config['tracing_mode'] = 'through'
config['reporter_host'] = '127.0.0.1'
config['reporter_port'] = 7831

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
        evt.addInfo('Backtrace', _str_backtrace()) # TODO get exception backtrace, not log backtrace

    if exception:
        evt.addInfo('ErrorClass', exception.__class__.__name__)
        evt.addInfo('ErrorMsg', str(exception))
    else:
        evt.addInfo('ErrorClass', err_class)
        evt.addInfo('ErrorMsg', err_msg)

    rep = reporter()
    return rep.sendReport(evt)

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
    def __init__(self, cls, profile_name, profile=False, store_backtrace=False):
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
            Context.log(None, 'error', ErrorClass=exc_type.__name__, ErrorMsg=str(exc_val), Backtrace=_str_backtrace(exc_tb))

        # build exit event
        exit_kvs = {}
        if self.use_cprofile and stats:
            exit_kvs['ProfileStats'] = stats
        exit_kvs['Language'] = 'python'
        exit_kvs['ProfileName'] = self.profile_name

        Context.log(None, 'profile_exit', **exit_kvs)

def profile_function(cls, profile_name, 
                   store_args=False, store_return=False, store_backtrace=False, profile=False, callback=None, **kwargs):
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
    @decorator
    def wrapper(func, *f_args, **f_kwargs):
        if not Context.isValid(): return func(*f_args, **f_kwargs)

        if store_args:
            kwargs.update({'Args': f_args, 'kwargs': f_kwargs })

        if 'im_class' in dir(func):
            kwargs['Class'] = func.im_class.__name__

        if not hasattr(func, '_oboe_file'): 
            setattr(func, '_oboe_file', inspect.getsourcefile(func))
        if not hasattr(func, '_oboe_line_number'): 
            setattr(func, '_oboe_line_number', inspect.getsourcelines(func)[1])
        if not hasattr(func, '_oboe_module'): 
            setattr(func, '_oboe_module', inspect.getmodule(func).__name__)
        if not hasattr(func, '_oboe_signature'): 
            setattr(func, '_oboe_signature', _function_signature(func))

        kwargs.update({'Language': 'python',
                       'ProfileName': profile_name,
                       'File': getattr(func, '_oboe_file'),
                       'LineNumber': getattr(func, '_oboe_line_number'),
                       'Module': getattr(func, '_oboe_module'),
                       'FunctionName': func.__name__,
                       'Signature': getattr(func, '_oboe_signature')})

        if store_backtrace:
            kwargs['Backtrace'] = _str_backtrace() 

        Context.log(None, 'profile_entry', **kwargs)

        try:
            res = None
            stats = None
            if profile and found_cprofile:
                p = cProfile.Profile()
                res = p.runcall(func, *f_args, **f_kwargs)

                sio = cStringIO.StringIO()
                s = pstats.Stats(p, stream=sio)
                s.sort_stats('time')
                s.print_stats(15)
                stats = sio.getvalue()
                sio.close()
            else:
                res = func(*f_args, **f_kwargs)
        except Exception, e:
            Context.log(None, 'error', ErrorClass=e.__class__.__name__, ErrorMsg=str(e))
            raise
        finally:
            exit_kvs = {}
            if callback and callable(callback):
                cb_kvs = callback(func, f_args, f_kwargs, res)
                if cb_kvs:
                    exit_kvs.update(cb_kvs)

            if store_return:
                exit_kvs['ReturnValue'] = res
            if profile and stats:
                exit_kvs['Profile'] = stats

            # XXX these redundant, though apparently necessary
            exit_kvs['Language'] = 'python'
            exit_kvs['ProfileName'] = profile_name

            Context.log(None, 'profile_exit', **exit_kvs)

        return res
    return wrapper

def log_method(cls, layer='Python',
               store_return=False, store_args=False, callback=None, profile=False, **kwargs):
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
    @decorator
    def wrap_method(func, *f_args, **f_kwargs):
        if not Context.isValid(): return func(*f_args, **f_kwargs)
        if store_args:
            kwargs.update( {'args' : f_args, 'kwargs': f_kwargs} )
        # log entry event
        Context.log(layer, 'entry', **kwargs)

        try:
            # call wrapped method
            res = None
            got_stats = False
            if profile and found_cprofile:
                p = cProfile.Profile()
                res = p.runcall(func, *f_args, **f_kwargs)

                sio = cStringIO.StringIO()
                s = pstats.Stats(p, stream=sio)
                s.sort_stats('time')
                s.print_stats(15)
                stats = sio.getvalue()
                sio.close()
                got_stats = True
            else:
                res = func(*f_args, **f_kwargs)
        except Exception, e:
            Context.log(layer, 'error', ErrorClass=e.__class__.__name__, Message=str(e))
            raise # reraise; finally still fires below
        finally:
            # call the callback function, if set, and merge its return
            # values with the exit event's reporting data
            exit_kvs = {}
            if callback and callable(callback):
                cb_ret = callback(func, f_args, f_kwargs, res)
                if cb_ret:
                    exit_kvs.update(cb_ret)

            # (optionally) report return value
            if store_return:
                exit_kvs['ReturnValue'] = str(res)

            # (optionally) store profiler results
            if got_stats:
                exit_kvs['Profile'] = stats

            # log exit event
            Context.log(layer, 'exit', **exit_kvs)
        return res

    return wrap_method

def reporter():
    global reporter_instance

    if not reporter_instance:
        reporter_instance = UdpReporter(config['reporter_host'], str(config['reporter_port']))

    return reporter_instance

setattr(Context, log.__name__, types.MethodType(log, Context))
setattr(Context, log_error.__name__, types.MethodType(log_error, Context))
setattr(Context, log_method.__name__, types.MethodType(log_method, Context))
setattr(Context, profile_function.__name__, types.MethodType(profile_function, Context))
setattr(Context, profile_block.__name__, types.MethodType(profile_block, Context))

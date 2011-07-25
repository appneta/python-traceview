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
        evt.addInfo('Backtrace', "".join(tb.format_list(tb.extract_stack()[:-1])))

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
        evt.addInfo('Backtrace', "".join(tb.format_list(tb.extract_stack()[:-1])))

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

def function_profile(cls, profile_name, 
                   store_args=False, store_return=False, profile=False, callback=None, **kwargs):
    """Wrap a method for tracing and profiling with the Tracelytics Oboe library.

          profile_name: the profile name to use when reporting.
          this should be unique to the profiled method.

          store_return: report the return value of this function

          store_args: report the arguments to this function

          profile: profile this function with cProfile and report the result

          callback: if set, calls this function after the wrapped
          function returns, which examines the function, arguments,
          and return value, and may add more K/V pairs to the
          dictionary to be reported

          Reports an error event between entry and exit if an
          exception is thrown, then reraises.

    """
    from functools import wraps
    def decorate(func):
        @wraps(func)
        def wrapper(*f_args, **f_kwargs):
            if not Context.isValid(): return func(*f_args, **f_kwargs)

            if store_args:
                kwargs.update({'Args': f_args, 'kwargs': f_kwargs })

            if 'im_class' in dir(func):
                kwargs.update({'Class': func.im_class.__name__})

            kwargs.update({'Language': 'python',
                           'ProfileName': profile_name,
                           'File': inspect.getsourcefile(func),
                           'LineNumber': inspect.getsourcelines(func)[1],
                           'Module': inspect.getmodule(func).__name__,
                           'FunctionName': func.__name__,
                           'Signature': _function_signature(func),
                           'Backtrace' : "".join(tb.format_stack()[:-1])})

            Context.log(None, 'profile_entry', **kwargs)

            try:
                res = None
                if profile:
                    try:
                        import cStringIO, cProfile, pstats
                    except ImportError:
                        res = func(*f_args, **f_kwargs)
                    
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
                    exit_kvs['ProfileStats'] = stats
               
                exit_kvs['Language'] = 'python'
                exit_kvs['ProfileName'] = profile_name

                Context.log(None, 'profile_exit', **exit_kvs)

            return res
        return wrapper
    return decorate

def log_method(cls, layer='Python',
               store_return=False, store_args=False, callback=None, profile=False, **kwargs):
<<<<<<< HEAD
    """ wrap a method for tracing with the Tracelytics Oboe library.
        as opposed to function_profile above, this decorator gives the method its own agent
=======
    """Wrap a method for tracing with the Tracelytics Oboe library.

        as opposed to profile_method, this decorator gives the method its own layer
>>>>>>> 7e6a04b86249ed0c89b9b9d67a0cdd69bcee5cff

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
    from functools import wraps
    def decorate(func):
        @wraps(func)
        def wrap_method(*f_args, **f_kwargs):
            if not Context.isValid(): return func(*f_args, **f_kwargs)
            if store_args:
                kwargs.update( {'args' : f_args, 'kwargs': f_kwargs} )
            # log entry event
            Context.log(layer, 'entry', **kwargs)

            try:
                # call wrapped method
                res = None
                got_stats = False
                if profile:
                    try:
                        import cStringIO, cProfile, pstats # XXX test cProfile and pstats exist
                    except ImportError:
                        res = func(*f_args, **f_kwargs)

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
    return decorate

def reporter():
    global reporter_instance

    if not reporter_instance:
        reporter_instance = UdpReporter(config['reporter_host'], str(config['reporter_port']))

    return reporter_instance

setattr(Context, log.__name__, types.MethodType(log, Context))
setattr(Context, log_error.__name__, types.MethodType(log_error, Context))
setattr(Context, log_method.__name__, types.MethodType(log_method, Context))
setattr(Context, function_profile.__name__, types.MethodType(function_profile, Context))

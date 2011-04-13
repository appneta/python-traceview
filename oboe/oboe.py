from oboe_ext import *

import types
import traceback as tb

__all__ = ['config', 'Context', 'UdpReporter', 'Event']

config = dict()
config['tracing_mode'] = 'through'
config['reporter_host'] = '127.0.0.1'
config['reporter_port'] = 7831

Context.init()

reporter_instance = None

def log(cls, agent, label, backtrace=False, **kwargs):
    if not Context.isValid(): return
    evt = Context.createEvent()
    evt.addInfo('Agent', agent)
    evt.addInfo('Label', label)
    if backtrace:
        evt.addInfo('Backtrace', "".join(tb.format_list(tb.extract_stack()[:-1])))

    for k, v in kwargs.items():
        evt.addInfo(str(k), str(v))

    rep = reporter()
    return rep.sendReport(evt)

def log_method(cls, agent='Python',
               store_return=False, store_args=False, callback=None, **kwargs):
    """ wrap a method for tracing with the Tracelytics Oboe library.
          agent: the agent to use when reporting

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
            Context.log(agent, 'entry', **kwargs)

            try:
                # call wrapped method
                res = func(*f_args, **f_kwargs)
            except Exception, e:
                oboe.Context.log('djangoORM', 'error', ErrorClass=e.__class__.__name__, Message=str(e))
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

                # log exit event
                Context.log(agent, 'exit', **exit_kvs)
                return res
        return wrap_method
    return decorate

def reporter():
    global reporter_instance

    if not reporter_instance:
        reporter_instance = UdpReporter(config['reporter_host'], str(config['reporter_port']))

    return reporter_instance

setattr(Context, log.__name__, types.MethodType(log, Context))
setattr(Context, log_method.__name__, types.MethodType(log_method, Context))

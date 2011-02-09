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

def log_method(cls, agent='Python', store_return=False, args_return=False, **kwargs):
    from functools import wraps
    def decorate(func):
        @wraps(func)
        def wrap_method(*f_args, **f_kwargs):
            if not Context.isValid(): return func(*f_args, **f_kwargs)
            if args_return:
                kwargs.update(f_kwargs)
                kwargs.update({'args' : f_args})
            Context.log(agent, 'entry', **kwargs)
            res = func(*f_args, **f_kwargs)
            if store_return:
                Context.log(agent, 'exit', ReturnValue=str(res))
            else:
                Context.log(agent, 'exit')
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

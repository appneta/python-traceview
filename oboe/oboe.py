from oboe_ext import *

import types
import traceback as tb

__all__ = ['config', 'Context', 'UdpReporter', 'MQReporter', 'Event']

config = dict()
config['tracing_mode'] = 'through'
config['reporter_host'] = '127.0.0.1'
config['reporter_port'] = 7831

Context.init()

reporter_instance = None

def log(cls, agent, label, **kwargs):
    evt = Context.createEvent()
    evt.addInfo('Agent', agent)
    evt.addInfo('Label', label)
    evt.addInfo('Backtrace', "".join(tb.format_list(tb.extract_stack()[:-1])))

    for k, v in kwargs.items():
        evt.addInfo(str(k), str(v))

    rep = reporter()
    return rep.sendReport(evt)

def log_method(cls, agent=None, store_return=False, **kwargs):
    if agent == None:
        agent = 'Python'
    def decorate(func):
        def methodcall(self, *f_args, **f_kwargs):
            kwargs.update(f_kwargs)
            kwargs.update({'args' : f_args})
            Context.log(agent, 'entry', **kwargs)
            res = func(self, *f_args, **f_kwargs)
            if store_return:
                Context.log(agent, 'exit', ReturnValue=str(res))
            else:
                Context.log(agent, 'exit')
            return res
        return methodcall
    return decorate

def reporter():
    global reporter_instance

    if not reporter_instance:
        reporter_instance = UdpReporter(config['reporter_host'], str(config['reporter_port']))

    return reporter_instance

setattr(Context, log.__name__, types.MethodType(log, Context))
setattr(Context, log_method.__name__, types.MethodType(log_method, Context))



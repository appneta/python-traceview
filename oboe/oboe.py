from oboe_ext import *

import types
import traceback as tb

__all__ = ['config', 'Context', 'UdpReporter', 'Event']

config = dict()
config['tracing_mode'] = 'through'
config['reporter_host'] = '127.0.0.1'


def log(cls, agent, label, **kwargs):
    evt = Context.createEvent()
    evt.addInfo('Agent', agent)
    evt.addInfo('Label', label)
    evt.addInfo('Backtrace', "".join(tb.format_list(tb.extract_stack()[:-1])))

    for k, v in kwargs.items():
        evt.addInfo(str(k), str(v))

    reporter = UdpReporter(config['reporter_host'])
    return reporter.sendReport(evt)

setattr(Context, log.__name__, types.MethodType(log, Context))

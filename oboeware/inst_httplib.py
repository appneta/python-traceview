""" Tracelytics instrumentation for requests.

Instrumentation is done in urllib3.

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
import sys
import oboe
import functools
from inst_http import wrap_request_after

HTTPLIB_LAYER = 'httplib'

def wrap_request_before(func, f_args, f_kwargs):
    if len(f_args) >= 1:
        self = f_args[0]
        self.putheader('x-trace', oboe.last_id())
    return f_args, f_kwargs, {}

def wrap(module):
    try:
        wrapper_before = oboe.log_method(HTTPLIB_LAYER,
                                         before_callback=wrap_request_before,
                                         send_exit_event=False)
        setattr(module.HTTPConnection, 'endheaders',
                wrapper_before(module.HTTPConnection.endheaders))

        after_cb = functools.partial(wrap_request_after, uri_position=None)
        wrapper_after = oboe.log_method(HTTPLIB_LAYER,
                                        callback=after_cb,
                                        send_entry_event=False)
        setattr(module.HTTPConnection, 'getresponse',
                wrapper_after(module.HTTPConnection.getresponse))
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)


try:
    import httplib
    wrap(httplib)
except ImportError, e:
    pass

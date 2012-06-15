""" Tracelytics instrumentation for httplib2.

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
import sys
import oboe
import functools
from inst_http import wrap_request_before, wrap_request_after

HTTPLIB2_LAYER = 'httplib2'

try:
    import httplib2
    try:
        before_cb = functools.partial(wrap_request_before, header_position=4)
        after_cb = functools.partial(wrap_request_after, uri_position=1)
        wrapper = oboe.Context.log_method(HTTPLIB2_LAYER,
                                          before_callback=before_cb,
                                          callback=after_cb)
        setattr(httplib2.Http, 'request', wrapper(httplib2.Http.request))
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)
except ImportError, e:
    pass


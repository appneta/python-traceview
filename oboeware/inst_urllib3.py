""" Tracelytics instrumentation for requests.

Instrumentation is done in urllib3.

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
import sys
import oboe
import functools
from inst_http import wrap_request_before, wrap_request_after

URLLIB3_LAYER = 'urllib3'

def wrap(module):
    try:
        before_cb = functools.partial(wrap_request_before, header_position=4)
        after_cb = functools.partial(wrap_request_after, uri_position=2)
        wrapper = oboe.log_method(URLLIB3_LAYER,
                                  before_callback=before_cb,
                                  callback=after_cb)
        setattr(module.connectionpool.HTTPConnectionPool, 'urlopen',
                wrapper(module.connectionpool.HTTPConnectionPool.urlopen))
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)


try:
    import urllib3
    wrap(urllib3)
except ImportError, e:
    pass

try:
    import requests.packages.urllib3
    wrap(requests.packages.urllib3)
except ImportError, e:
    pass

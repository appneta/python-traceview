""" Tracelytics instrumentation for httplib2.

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
import sys
import oboe
from  urlparse import urlparse

HTTPLIB2_LAYER = 'httplib2'

def wrap_request_before(func, f_args, f_kwargs):
    if len(f_args) > 5:
        headers = f_args[4]
        from_f_args = True
    else:
        headers = f_kwargs['headers']
        from_f_args = False
    if headers is None:
        headers = {}
    if not 'X-Trace' in headers:
        headers['X-Trace'] = oboe.Context.toString()
    if from_f_args:
        f_args = list(f_args)
        f_args[4] = headers
    else:
        f_kwargs['headers'] = headers
    return f_args, f_kwargs, {}

def wrap_request_after(func, f_args, f_kwargs, res):
    info = urlparse(f_args[1])
    path = info.path
    if path == '':
        path = '/'
    if info.query != '':
        path += '?' + info.query

    return {'IsService': 'yes',
            'RemoteProtocol': info.scheme if info.scheme != '' else 'http', # XXX Not Python2.4-friendly
            'RemoteHost': info.netloc,
            'ServiceArg': path}

try:
    import httplib2
    try:
        wrapper = oboe.Context.log_method(HTTPLIB2_LAYER,
                                          before_callback=wrap_request_before,
                                          callback=wrap_request_after)
        setattr(httplib2.Http, 'request', wrapper(httplib2.Http.request))
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)
except ImportError, e:
    pass


"""Module for instrumenting HTTP libraries (httplib2, urllib3).

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
import oboe
from urlparse import urlparse

def wrap_request_before(func, f_args, f_kwargs, header_position):
    if len(f_args) > header_position + 1:
        headers = f_args[header_position]
        from_f_args = True
    else:
        headers = f_kwargs['headers']
        from_f_args = False
    if headers is None:
        headers = {}
    if not 'X-Trace' in headers:
        headers['X-Trace'] = oboe.toString()
    if from_f_args:
        f_args = list(f_args)
        f_args[header_position] = headers
    else:
        f_kwargs['headers'] = headers
    return f_args, f_kwargs, {}

def wrap_request_after(func, f_args, f_kwargs, res, uri_position):
    info = urlparse(f_args[uri_position])
    path = info.path
    if path == '':
        path = '/'
    if info.query != '':
        path += '?' + info.query

    return {'IsService': 'yes',
            'RemoteProtocol': info.scheme if info.scheme != '' else 'http', # XXX Not Python2.4-friendly
            'RemoteHost': info.netloc,
            'ServiceArg': path}

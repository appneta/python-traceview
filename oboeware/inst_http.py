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
        headers['X-Trace'] = oboe.last_id()
    if from_f_args:
        f_args = list(f_args)
        f_args[header_position] = headers
    else:
        f_kwargs['headers'] = headers
    return f_args, f_kwargs, {}

def wrap_request_after(func, f_args, f_kwargs, res, uri_position):
    path = None
    info = None
    if uri_position is not None:
        info = urlparse(f_args[uri_position])
        path = info.path
        if path == '':
            path = '/'
        if info.query != '':
            path += '?' + info.query

    edge_str = None
    if res:
        headers = None
        if isinstance(res, tuple) and len(res) == 2:
            # httplib2:
            headers = res[0]
        elif hasattr(res, 'headers'):
            # urllib3:
            headers = res.headers
        elif hasattr(res, 'getheader'):
            # httplib:
            edge_str = res.getheader('x-trace')

        if headers:
            edge_str = hasattr(headers, 'get') and headers.get('x-trace', None)

    return ({'IsService': 'yes',
             'RemoteProtocol': info and (info.scheme if info.scheme != '' else 'http'), # XXX Not Python2.4-friendly
             'RemoteHost': info and info.netloc,
             'ServiceArg': path},
             edge_str)

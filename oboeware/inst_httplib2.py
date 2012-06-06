""" Tracelytics instrumentation for httplib2.

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
import sys
import oboe
from  urlparse import urlparse

HTTPLIB2_LAYER = 'httplib2'

def wrap(module):
    try:
        real_request = module.Http.request
        from functools import wraps
        @wraps(module.Http.request)
        def wrapped_request(self, uri, method="GET", body=None, headers=None, redirections=5, connection_type=None):
            if not headers:
                headers = {}
            if oboe.Context.isValid():
                evt = oboe.Context.createEvent()
                info = urlparse(uri)
                evt.addInfo('IsService', 'yes')
                evt.addInfo('RemoteProtocol', info.scheme if info.scheme != '' else 'http')
                evt.addInfo('RemoteHost', info.netloc)

                path = info.path
                if path == '':
                    path = '/'
                if info.query != '':
                    path += '?' + info.query
                evt.addInfo('ServiceArg', path)

                evt.addInfo('Layer', HTTPLIB2_LAYER)
                evt.addInfo('Label', 'entry')
                reporter = oboe.reporter().sendReport(evt)
                response = None
                try:
                    if not 'X-Trace' in headers:
                        headers['X-Trace'] = oboe.Context.toString()
                    response = real_request(self, uri, method=method, body=body,
                                            headers=headers, redirections=redirections,
                                            connection_type=connection_type)
                except Exception, exc:
                    oboe.Context.log_exception()
                finally:
                    evt = oboe.Context.createEvent()
                    evt.addInfo('Layer', HTTPLIB2_LAYER)
                    evt.addInfo('Label', 'exit')
                    reporter = oboe.reporter().sendReport(evt)
                return response
            else:
                return real_request(self, uri, method=method, body=body,
                                    headers=headers, redirections=redirections,
                                    connection_type=connection_type)

        setattr(module.Http,'request', wrapped_request)

    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

try:
    import httplib2
    wrap(httplib2)
except ImportError, e:
    pass


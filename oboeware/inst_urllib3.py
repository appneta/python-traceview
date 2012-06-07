""" Tracelytics instrumentation for requests.

Instrumentation is done in urllib3.

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
import sys
import oboe
from  urlparse import urlparse

URLLIB3_LAYER = 'urllib3'

def wrap(module):
    try:
        real_urlopen =  module.connectionpool.HTTPConnectionPool.urlopen
        from functools import wraps
        @wraps(real_urlopen) # XXX Not Python2.4-friendly
        def wrapped_urlopen(self, method, url, body=None, headers=None, retries=3,
                redirect=True, assert_same_host=True,
                pool_timeout=None, release_conn=None, **response_kw):
            if oboe.Context.isValid():
                if not headers:
                    headers = {}
                evt = oboe.Context.createEvent()
                info = urlparse(url)
                evt.addInfo('IsService', 'yes')
                evt.addInfo('RemoteProtocol', info.scheme if info.scheme != '' else 'http') # XXX Not Python2.4-friendly
                evt.addInfo('RemoteHost', info.netloc)

                path = info.path
                if path == '':
                    path = '/'
                if info.query != '':
                    path += '?' + info.query
                evt.addInfo('ServiceArg', path)

                evt.addInfo('Layer', URLLIB3_LAYER)
                evt.addInfo('Label', 'entry')
                reporter = oboe.reporter().sendReport(evt)
                response = None
                try:
                    if not 'X-Trace' in headers:
                        headers['X-Trace'] = oboe.Context.toString()
                    response = real_urlopen(self, method, url, body=body, headers=headers, retries=retries,
                                                redirect=redirect, assert_same_host=assert_same_host,
                                                pool_timeout=pool_timeout, release_conn=release_conn, **response_kw)
                except Exception, exc:
                    oboe.Context.log_exception()
                finally: # XXX Not Python2.4-friendly
                    evt = oboe.Context.createEvent()
                    evt.addInfo('Layer', URLLIB3_LAYER)
                    evt.addInfo('Label', 'exit')
                    reporter = oboe.reporter().sendReport(evt)
                return response
            else:
                return real_urlopen(self, method, url, body=body, headers=headers, retries=retries,
                                        redirect=redirect, assert_same_host=assert_same_host,
                                        pool_timeout=pool_timeout, release_conn=release_conn, **response_kw)

        setattr(module.connectionpool.HTTPConnectionPool,'urlopen', wrapped_urlopen)

    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

try:
    import urllib3
    wrap(urllib3)
except ImportError, e:
    pass

# requests packages urllib3 internally for some reason
try:
    import requests.packages.urllib3
    wrap(requests.packages.urllib3)
except ImportError, e:
    pass

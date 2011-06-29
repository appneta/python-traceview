# Copyright (C) 2011 by Tracelytics, Inc.
# All rights reserved.

import sys
import oboe

HTTPLIB2_AGENT = 'remote_request'

def wrap(module):
    try:
        real_request = module.Http.request
        from functools import wraps 
        @wraps(module.Http.request)
        def wrapped_request(self, uri, method="GET", body=None, headers=None, redirections=5, connection_type=None):
            if not headers:
                headers = {}
            evt = oboe.Context.createEvent()
            evt.addInfo('Agent', HTTPLIB2_AGENT)
            evt.addInfo('Label', 'entry')
            reporter = oboe.reporter().sendReport(evt)
            try:
                if not 'XTrace' in headers:
                    headers['XTrace'] = oboe.Context.toString()
                response = real_request(self, uri, method=method, body=body,
                                        headers=headers, redirections=redirections,
                                        connection_type=connection_type)
            except e:
                evt = oboe.Context.createEvent()
                evt.addInfo('Agent', HTTPLIB2_AGENT)
                evt.addInfo('Label', 'error')
                evt.addInfo('ErrorMsg', str(e))
                evt.addInfo('ErrorClass', e.__class__.__name__)
                reporter = oboe.reporter().sendReport(evt)
            finally:
                evt = oboe.Context.createEvent()
                evt.addInfo('Agent', HTTPLIB2_AGENT)
                evt.addInfo('Label', 'exit')
                reporter = oboe.reporter().sendReport(evt)
            return response

        setattr(module.Http,'request', wrapped_request)

    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)


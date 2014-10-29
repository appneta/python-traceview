""" WSGI middleware for Oboe support

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""

import oboe
import sys
from loader import load_inst_modules
import oninit
import traceback as tb

MODULE_INIT_REPORTED = False

class OboeMiddleware(object):
    def __init__(self, app, oboe_config=None, layer="wsgi", profile=False):
        """
        Install instrumentation for tracing a WSGI app.

        Arguments:
            app - the WSGI app that we're wrapping
            oboe_config - (optional) dictionary with oboe configuration parameters:
              - oboe.tracing_mode: 'always', 'through', 'never'
              - oboe.sample_rate: a number from 0 to 1000000 denoting fraction of requests to trace
            layer - (optional) layer name to use, default is "wsgi"
            profile - (optional) profile entire calls to app (don't use in production)
        """
        if oboe_config == None:
            oboe_config = {}

        self.wrapped_app = app
        self.oboe_config = oboe_config
        self.layer = layer
        self.profile = profile

        if self.oboe_config.get('oboe.tracing_mode'):
            oboe.config['tracing_mode'] = self.oboe_config['oboe.tracing_mode']

        if self.oboe_config.get('oboe.reporter_host'):
            oboe.config['reporter_host'] = self.oboe_config['oboe.reporter_host']

        if self.oboe_config.get('oboe.reporter_port'):
            oboe.config['reporter_port'] = self.oboe_config['oboe.reporter_port']

        if self.oboe_config.get('oboe.sample_rate'):
            oboe.config['sample_rate'] = float(self.oboe_config['oboe.sample_rate'])

        # load pluggaable instrumentation
        load_inst_modules()

        # phone home
        global MODULE_INIT_REPORTED
        if not MODULE_INIT_REPORTED:
            oninit.report_layer_init()
            MODULE_INIT_REPORTED = True

    def __call__(self, environ, start_response):
        xtr_hdr = environ.get("HTTP_X-Trace", environ.get("HTTP_X_TRACE"))
        avw_hdr = environ.get("HTTP_X-TV-Meta", environ.get('HTTP_X_TV_META'))
        endEvt = None

        # start the trace: ctx.is_valid() will be False if not tracing this request
        ctx, startEvt = oboe.Context.start_trace(self.layer, xtr=xtr_hdr, avw=avw_hdr)

        if ctx.is_valid():
            # get some HTTP details from WSGI vars
            # http://www.wsgi.org/en/latest/definitions.html
            for hosthdr in ("HTTP_HOST", "HTTP_X_HOST", "HTTP_X_FORWARDED_HOST", "SERVER_NAME"):
                if hosthdr in environ:
                    startEvt.add_info("HTTP-Host", environ[hosthdr])
                    break
            if 'PATH_INFO' in environ:
                startEvt.add_info("URL", environ['PATH_INFO'])
            if 'REQUEST_METHOD' in environ:
                startEvt.add_info("Method", environ['REQUEST_METHOD'])
            if 'QUERY_STRING' in environ:
                startEvt.add_info("Query-String", environ['QUERY_STRING'])

            ctx.report(startEvt)
            endEvt = ctx.create_event('exit', self.layer)
            ctx.set_as_default()

        response_body = []
        def wrapped_start_response(status, headers, exc_info=None):
            if ctx.is_valid():
                headers.append(("X-Trace", endEvt.id()))
                endEvt.add_info("Status", status.split(' ', 1)[0])
                if exc_info:
                    _t, exc, trace = exc_info
                    endEvt.add_info("ErrorMsg", str(exc))
                    endEvt.add_info("ErrorClass", exc.__class__.__name__)
                    endEvt.add_info("Backtrace", "".join(tb.format_list(tb.extract_tb(trace))))
            start_response(status, headers)
            if self.profile:
                return response_body.append

        stats = None
        result = None
        try:
            if self.profile and ctx.is_valid():
                try:
                    import cStringIO, cProfile, pstats # XXX test cProfile and pstats exist
                except ImportError:
                    self.profile = False

            if self.profile and ctx.is_valid():
                def runapp():
                    appiter = self.wrapped_app(environ, wrapped_start_response)
                    response_body.extend(appiter)
                    if hasattr(appiter, 'close'):
                        appiter.close()

                p = cProfile.Profile()
                p.runcall(runapp)
                body = ''.join(response_body)
                result = [body]

                sio = cStringIO.StringIO()
                s = pstats.Stats(p, stream=sio)
                s.sort_stats('cumulative')
                s.print_stats(15)
                stats = sio.getvalue()
                sio.close()
            else:
                result = self.wrapped_app(environ, wrapped_start_response)

        except Exception:
            if oboe.Context.get_default().is_valid():
                endEvt.add_edge(oboe.Context.get_default())
            self.send_end(ctx, endEvt, environ, threw_error=True)
            raise

        # check current TLS context and add to end event if valid
        if oboe.Context.get_default().is_valid():
            endEvt.add_edge(oboe.Context.get_default())

        self.send_end(ctx, endEvt, environ, stats=stats)

        return result

    @classmethod
    def send_end(cls, ctx, evt, environ, threw_error=None, stats=None):
        if not ctx.is_valid():
            return

        evt.add_edge(ctx)
        if stats:
            evt.add_info("Profile", stats)
        if threw_error:
            _t, exc, trace = sys.exc_info()
            evt.add_info("ErrorMsg", str(exc))
            evt.add_info("ErrorClass", exc.__class__.__name__)
            evt.add_info("Backtrace", "".join(tb.format_list(tb.extract_tb(trace))))
            del trace # delete reference to traceback object to allow garbage collection

        # gets controller, action
        for k, v in environ.get('wsgiorg.routing_args', [{},{}])[1].items():
            if k == "action":
                 evt.add_info(str(k).capitalize(), str(v))
            elif k == "controller":
                try:
                    # handle cases used in openstack's WSGI (and possibly others)
                    if v.controller:
                        evt.add_info(str(k).capitalize(), str(v.controller.__class__.__name__))
                    else:
                        evt.add_info(str(k).capitalize(), str(v))
                except Exception:
                    evt.add_info(str(k).capitalize(), str(v))

        # report, then clear trace context now that trace is over
        ctx.end_trace(evt)
        oboe.Context.clear_default()

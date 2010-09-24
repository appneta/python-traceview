# WSGI middleware for Oboe support
import oboe
MEM_TRACE = False
try:
    import muppy
    MEM_TRACE = True
except ImportError:
    pass

class OboeMiddleware:
    def __init__(self, app, oboe_config):
        """
        Takes the app that we're wrapping, as well as a dictionary with oboe
        configuration parameters:

          - tracing_mode: 'always', 'through', 'never'
          - reporter_host: Hostname
        """

        self.wrapped_app = app
        self.oboe_config = oboe_config

    def __call__(self, environ, start_response):
        xtr_hdr = environ.get("HTTP_X-Trace", environ.get("HTTP_X_TRACE"))
        evt, endEvt = None, None
        mem_tracker = None
        
        tracing_mode = self.oboe_config.get('oboe.tracing_mode')

        if xtr_hdr and tracing_mode in ['always', 'through']:
            oboe.Context.fromString(xtr_hdr)

        if not oboe.Context.isValid() and tracing_mode == "always":
            evt = oboe.Context.startTrace()
        elif oboe.Context.isValid() and tracing_mode != 'never':
            evt = oboe.Context.createEvent()

        if oboe.Context.isValid() and tracing_mode != 'never':
            evt.addInfo("Agent", "wsgi")
            evt.addInfo("Label", "entry")
            reporter = oboe.UdpReporter(self.oboe_config.get('oboe.reporter_host'))
            reporter.sendReport(evt)

            endEvt = oboe.Context.createEvent()

            add_header = True
            mem_tracker = muppy.tracker.SummaryTracker() if MEM_TRACE else None
        else:
            add_header = False

        
        def wrapped_start_response(status, headers):
            if add_header: headers.append(("X-Trace", endEvt.metadataString()))
            start_response(status, headers)

        result = self.wrapped_app(environ, wrapped_start_response)

        # TODO: Should we handle starting a trace here?
        if oboe.Context.isValid() and tracing_mode != 'never' and endEvt:
            mem_diff = mem_tracker.diff() if mem_tracker else None
            evt = endEvt

            evt.addEdge(oboe.Context.get())
            evt.addInfo("Agent", "wsgi")
            evt.addInfo("Label", "exit")
            evt.addInfo("Memory-Diff", mem_diff)

            # gets controller, agent
            for k, v in  environ.get('wsgiorg.routing_args')[1].items():
                evt.addInfo(str(k).capitalize(), str(v))

            reporter = oboe.UdpReporter(self.oboe_config.get('oboe.reporter_host'))
            reporter.sendReport(evt)
            
            endEvt = None

        return result

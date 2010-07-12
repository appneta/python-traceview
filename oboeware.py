# WSGI middleware for Oboe support
import oboe

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
        xtr_hdr = environ.get("HTTP_X-Trace")
        evt, endEvt = None, None

        tracing_mode = self.oboe_config.get('oboe.tracing_mode')

        if xtr_hdr and tracing_mode in ['always', 'through']:
            oboe.Context.fromString(xtr_hdr)

        if not oboe.Conext.isValid() and tracing_mode == "always":
            evt = oboe.Context.startTrace()
        elif oboe.Context.isValid() and tracing_mode != 'never':
            evt = oboe.Context.createEvent()

        if oboe.Context.isValid() and tracing_mode != 'never':
            evt.addInfo("Agent", "wsgi")
            evt.addInfo("Label", "entry")

            reporter = oboe.UdpReporter(self.oboe_config.get('oboe.reporter_host'))
            reporter.sendReport(evt)

            endEvt = oboe.Context.createEvent()

        result = self.wrapped_app(environ, start_response)

        # TODO: Should we handle starting a trace here?
        if oboe.Context.isValid() and tracing_mode != 'never' and endEvt:
            evt = endEvt

            evt.addEdge(oboe.Context.get())
            evt.addInfo("Agent", "wsgi")
            evt.addInfo("Label", "exit")

            reporter = oboe.UdpReporter(self.oboe_config.get('oboe.reporter_host'))
            reporter.sendReport(evt)
            
            environ["HTTP_X-Trace"] = oboe.Context.toString()
            endEvt = nil

        return result

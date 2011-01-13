# WSGI middleware for Oboe support
import oboe
import sys

class OboeMiddleware:
    def __init__(self, app, oboe_config, agent="wsgi"):
        """
        Takes the app that we're wrapping, as well as a dictionary with oboe
        configuration parameters:

          - tracing_mode: 'always', 'through', 'never'
          - reporter_host: Hostname
        """

        self.wrapped_app = app
        self.oboe_config = oboe_config
        self.agent = agent

        if self.oboe_config.get('oboe.tracing_mode'):
            oboe.config['tracing_mode'] = self.oboe_config['oboe.tracing_mode']

        if self.oboe_config.get('oboe.reporter_host'):
            oboe.config['reporter_host'] = self.oboe_config['oboe.reporter_host']

        if self.oboe_config.get('oboe.reporter_port'):
            oboe.config['reporter_port'] = self.oboe_config['oboe.reporter_port']

    def __call__(self, environ, start_response):
        xtr_hdr = environ.get("HTTP_X-Trace", environ.get("HTTP_X_TRACE"))
        evt, endEvt = None, None
        
        tracing_mode = self.oboe_config.get('oboe.tracing_mode')

        # Check for existing context: pylons errors with debug=false result in
        # a second wsgi entry.  Using the existing context is favorable in
        # that case.
        if not oboe.Context.isValid() and xtr_hdr and tracing_mode in ['always', 'through']:
            oboe.Context.fromString(xtr_hdr)

        if not oboe.Context.isValid() and tracing_mode == "always":
            evt = oboe.Context.startTrace()
        elif oboe.Context.isValid() and tracing_mode != 'never':
            evt = oboe.Context.createEvent()

        if oboe.Context.isValid() and tracing_mode != 'never':
            evt.addInfo("Agent", self.agent)
            evt.addInfo("Label", "entry")
            reporter = oboe.reporter().sendReport(evt)

            endEvt = oboe.Context.createEvent()

            add_header = True
        else:
            add_header = False
        
        def wrapped_start_response(status, headers, exc_info=None):
            if add_header:
                headers.append(("X-Trace", endEvt.metadataString()))
                if exc_info:
                    import traceback as tb
                    (t, exc, trace) = exc_info
                    endEvt.addInfo("Error", repr(exc))
                    endEvt.addInfo("Backtrace", "".join(tb.format_list(tb.extract_tb(trace))))
            start_response(status, headers)

        try:
            result = self.wrapped_app(environ, wrapped_start_response)
        except Exception, e:
            self.send_end(tracing_mode, endEvt, environ, True, agent=self.agent)
            raise

        self.send_end(tracing_mode, endEvt, environ, agent=self.agent)
        oboe.Context.clear()

        return result

    @classmethod
    def send_end(cls, tracing_mode, endEvt, environ, threw_error=None, agent="wsgi"):
        if oboe.Context.isValid() and tracing_mode != 'never' and endEvt:
            evt = endEvt

            evt.addEdge(oboe.Context.get())
            evt.addInfo("Agent", agent)
            evt.addInfo("Label", "exit")
            if threw_error:
                import traceback as tb
                (t, exc, trace) = sys.exc_info()
                evt.addInfo("Error", repr(exc))
                evt.addInfo("Backtrace", "".join(tb.format_list(tb.extract_tb(trace))))

            # gets controller, agent
            for k, v in  environ.get('wsgiorg.routing_args', [{},{}])[1].items():
                evt.addInfo(str(k).capitalize(), str(v))

            reporter = oboe.reporter().sendReport(evt)

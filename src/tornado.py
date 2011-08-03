# useful methods for instrumenting Tornado
# (c) 2011 Tracelytics, Inc.
import oboe

# instrumentation functions for tornado.web.RequestHandler
def RequestHandler_start(self):
    """ runs from the main HTTP server thread (doesn't set/get Context) """
    xtr = self.request.headers.get("X-Trace", None)
    if xtr:
        md = oboe.Metadata.fromString(xtr)
        ev = md.createEvent() # adds edge to X-Trace header
    else:
        md = oboe.Metadata.makeRandom()
        ev = oboe.Event.startTrace(md)

    ev.addInfo("Layer", "tornado")
    ev.addInfo("Label", "entry")
    if hasattr(self, '__class__') and hasattr(self.__class__, '__name__'):
        ev.addInfo("Controller", self.__class__.__name__)
        ev.addInfo("Action", self.request.method.lower())
    ev.addInfo("URL", self.request.uri)
    ev.addInfo("Method", self.request.method)
    ev.addInfo("HTTP-Host", self.request.host)
    ret = oboe.reporter().sendReport(ev, md) # sets md = ev.metadata

    # create & store finish event for reporting later
    self.request._oboe_md = md
    self.request._oboe_finish_ev = md.createEvent() # adds edge from exit event -> enter event's md

    # report the exit event ID in the response header
    self.set_header("X-Trace", self.request._oboe_finish_ev.metadataString())

def RequestHandler_finish(self):
    """ runs from the main HTTP server thread, or from write/flush() callback 
        doesn't set/get Context; just checks if finish event was set by oboe_start()
    """
    if self.request._oboe_finish_ev and self.request._oboe_md:
        self.request._oboe_finish_ev.addInfo("Layer", "tornado")
        self.request._oboe_finish_ev.addInfo("Label", "exit")
        if hasattr(self, 'get_status'):
            self.request._oboe_finish_ev.addInfo("Status", self.get_status())
        elif hasattr(self, '_status_code'):
            self.request._oboe_finish_ev.addInfo("Status", self._status_code)

        # XXX add edge from context/RequestHandler -> exit
        # self.request._oboe_finish_ev.addEdge(self.request._oboe_md)
        oboe.reporter().sendReport(self.request._oboe_finish_ev, self.request._oboe_md)

        # clear the stored oboe event/metadata from the request object
        self.request._oboe_md = None
        self.request._oboe_finish_ev = None

# instrumentation for tornado.httpclient.AsyncHTTPClient
def AsyncHTTPClient_start(request):
    oboe.Context.log("cURL", "entry", True, cURL_URL=request.url)
    request._oboe_md = oboe.Context.copy()

def AsyncHTTPClient_finish(request):
    if hasattr(request, '_oboe_md'):
        ev = request._oboe_md.createEvent() # adds edge to md
        ev.addInfo("Layer", "cURL")
        ev.addInfo("Label", "exit")
        # ev.addEdge(oboe.Context.get()) # this is not the right edge.
        oboe.reporter().sendReport(ev, request._oboe_md)
        # this branch of the trace graph is ending: do nothing with req._oboe_md?

# used for wrapping stack contexts in tornado.stack_context
class OboeContextWrapper(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped
        if oboe.Context.isValid():
            ctx = oboe.Context.copy()
            self._oboe_md = ctx

    def __call__(self, *args, **kwargs):
        import async
        with async.OboeContextManager(self):
            return self.wrapped.__call__(*args, **kwargs)

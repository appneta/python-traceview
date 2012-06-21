""" Tracelytics instrumentation for Tornado.

Copyright (C) 2012 by Tracelytics, Inc.
All rights reserved.
"""
# useful methods for instrumenting Tornado
from __future__ import with_statement
import oboe
from oboeware import async

# instrumentation functions for tornado.web.RequestHandler
def RequestHandler_start(self):
    """ runs from the main HTTP server thread (doesn't set/get Context)

        takes 'self' parameter, which is the current RequestHandler
        instance (which holds the current HTTPRequest in self.request)
    """
    # check for X-Trace header in HTTP request
    xtr = self.request.headers.get("X-Trace", None)
    if xtr: # add edge to incoming X-Trace header
        md = oboe.Metadata.fromString(xtr)
        ev = md.createEvent()
    else:   # start a new trace
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
        if hasattr(self, 'get_status'): # recent Tornado
            self.request._oboe_finish_ev.addInfo("Status", self.get_status())
        elif hasattr(self, '_status_code'): # older Tornado
            self.request._oboe_finish_ev.addInfo("Status", self._status_code)

        if oboe.Context.isValid():
            self.request._oboe_finish_ev.addEdge(oboe.Context.get())

        oboe.reporter().sendReport(self.request._oboe_finish_ev, self.request._oboe_md)

        # clear the stored oboe event/metadata from the request object
        self.request._oboe_md = None
        self.request._oboe_finish_ev = None

# instrumentation for tornado.httpclient.AsyncHTTPClient
def AsyncHTTPClient_start(request):
    """ takes 'request' param, which is the outgoing HTTPRequest, not the request currently being handled """
    # this is called from AsyncHTTPClient.fetch(), which runs from the RequestHandler's context
    oboe.log("cURL", "entry", True, {'cURL_URL':request.url, 'Async':True})
    if hasattr(request, 'headers'):
        if (hasattr(request.headers, '__setitem__')): # could be dict or tornado.httputil.HTTPHeaders
            request.headers['X-Trace'] = oboe.Context.toString() # add X-Trace header to outgoing request

    request._oboe_md = oboe.Context.copy()

def AsyncHTTPClient_finish(request, callback=None, headers=None):
    """
    fires exit event for Async HTTP requests.

    checks for wrapped metadata stored in user's callback function: if
    it exists, that metadata is used & updated when reporting the
    event, so that the callback will "happen after" the exit event.
    """
    if hasattr(callback, '_oboe_md'):        # wrapped callback contains md
        ev = callback._oboe_md.createEvent() # adds edge to md
        if hasattr(request, '_oboe_md'):     # add edge to entry event for this async HTTP call
            ev.addEdge(request._oboe_md)
        mdobj = callback

    elif hasattr(request, '_oboe_md'):       # callback contains no metadata, but request obj does
        ev = request._oboe_md.createEvent()
        mdobj = request

    else: # no metadata found
        return

    if headers and hasattr(headers, 'get') and headers.get('X-Trace', None):
        response_md = oboe.Metadata.fromString(headers.get('X-Trace'))
        ev.addEdge(response_md) # add response X-Trace header

    ev.addInfo("Layer", "cURL")
    ev.addInfo("Label", "exit")
    oboe.reporter().sendReport(ev, mdobj._oboe_md) # increments metadata in mdobj

# used for wrapping stack contexts in Tornado v1.2 stack_context.py
class OboeContextWrapper(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped
        if oboe.Context.isValid(): # get current context at wrap time (e.g. when preparing "done" callback for an async call)
            self._oboe_md = oboe.Context.copy() # store wrap-time context for use at call time

    def __call__(self, *args, **kwargs):
        with async.OboeContextManager(self): # uses self._oboe_md as context
            return self.wrapped.__call__(*args, **kwargs)

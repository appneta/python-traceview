""" Tracelytics instrumentation for Tornado.

Copyright (C) 2012 by Tracelytics, Inc.
All rights reserved.
"""
# useful methods for instrumenting Tornado
from __future__ import with_statement
import oboe
from oboeware import async
from oboeware import oninit
import functools
    
oninit.report_layer_init(layer='tornado')

# instrumentation functions for tornado.web.RequestHandler
def RequestHandler_start(self):
    """ runs from the main HTTP server thread (doesn't set/get Context)

        takes 'self' parameter, which is the current RequestHandler
        instance (which holds the current HTTPRequest in self.request)
    """
    # check for X-Trace header in HTTP request
    ctx, ev = oboe.Context.start_trace('tornado', xtr=self.request.headers.get("X-Trace"), avw=self.request.headers.get("X-TV-Meta"))

    if hasattr(self, '__class__') and hasattr(self.__class__, '__name__'):
        ev.add_info("Controller", self.__class__.__name__)
        ev.add_info("Action", self.request.method.lower())
    ev.add_info("URL", self.request.uri)
    ev.add_info("Method", self.request.method)
    ev.add_info("HTTP-Host", self.request.host)
    ctx.report(ev)

    # create & store finish event for reporting later
    self.request._oboe_ctx = ctx
    self.request._oboe_finish_ev = ctx.create_event('exit', 'tornado') # adds edge from exit event -> enter event's md

    # report the exit event ID in the response header
    self.set_header("X-Trace", self.request._oboe_finish_ev.id())

def RequestHandler_finish(self):
    """ runs from the main HTTP server thread, or from write/flush() callback
        doesn't set/get Context; just checks if finish event was set by oboe_start()
    """
    if self.request._oboe_finish_ev and self.request._oboe_ctx and self.request._oboe_ctx.is_valid():
        ev = self.request._oboe_finish_ev
        ctx = self.request._oboe_ctx
        if hasattr(self, 'get_status'): # recent Tornado
            ev.add_info("Status", self.get_status())
        elif hasattr(self, '_status_code'): # older Tornado
            ev.add_info("Status", self._status_code)

        ev.add_edge(oboe.Context.get_default())
        ctx.report(ev)

    # clear the stored oboe event/metadata from the request object
    self.request._oboe_ctx = None
    self.request._oboe_finish_ev = None

# instrumentation for tornado.httpclient.AsyncHTTPClient
def AsyncHTTPClient_start(request):
    """ takes 'request' param, which is the outgoing HTTPRequest, not the request currently being handled """
    # this is called from AsyncHTTPClient.fetch(), which runs from the RequestHandler's context
    oboe.log("entry", "cURL", keys={'cURL_URL':request.url, 'Async':True})
    ctx = oboe.Context.get_default()
    if hasattr(request, 'headers'):
        if (hasattr(request.headers, '__setitem__')): # could be dict or tornado.httputil.HTTPHeaders
            request.headers['X-Trace'] = str(ctx) # add X-Trace header to outgoing request

    request._oboe_ctx = ctx.copy()

def AsyncHTTPClient_finish(request, callback=None, headers=None):
    """
    fires exit event for Async HTTP requests.

    checks for wrapped metadata stored in user's callback function: if
    it exists, that metadata is used & updated when reporting the
    event, so that the callback will "happen after" the exit event.
    """
    if hasattr(callback, '_oboe_ctx'):                       # wrapped callback contains md
        ev = callback._oboe_ctx.create_event('exit', 'cURL') # adds edge to md
        if hasattr(request, '_oboe_ctx'):                    # add edge to entry event for this async HTTP call
            ev.add_edge(request._oboe_ctx)
        mdobj = callback

    elif hasattr(request, '_oboe_ctx'):                      # callback contains no metadata, but request obj does
        ev = request._oboe_ctx.create_event('exit', 'cURL')
        mdobj = request

    else: # no metadata found
        return

    if headers and hasattr(headers, 'get') and headers.get('X-Trace', None):
        response_md = headers.get('X-Trace')
        ev.add_edge_str(response_md) # add response X-Trace header

    mdobj._oboe_ctx.report(ev) # increments metadata in mdobj

# used for wrapping stack contexts in Tornado v1.2 stack_context.py
class OboeContextWrapper(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped
        # get current context at wrap time (e.g. when preparing "done" callback for an async call)
        if oboe.Context.get_default().is_valid():
            # store wrap-time context for use at call time
            self._oboe_ctx = oboe.Context.get_default().copy()

    def __call__(self, *args, **kwargs):
        with async.OboeContextManager(self): # uses self._oboe_ctx as context
            return self.wrapped.__call__(*args, **kwargs)

# replacement for _StackContextWrapper in Tornado v2.x stack_context.py
class _StackContextWrapper(functools.partial):
    def __init__(self, *args, **kwargs):
        if oboe.Context.get_default().is_valid():
            self._oboe_ctx = oboe.Context.get_default().copy()
        return super(_StackContextWrapper, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        with async.OboeContextManager(self):
            return super(_StackContextWrapper, self).__call__(*args, **kwargs)

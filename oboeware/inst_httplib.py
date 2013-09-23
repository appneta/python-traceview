""" Tracelytics instrumentation for requests.

Instrumentation is done in urllib3.

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
import sys
import oboe

def safeindex(_list, index):
    return _list[index] if len(_list) > index else None

def safeget(obj, key):
    return obj.get(key, None) if obj and hasattr(obj, 'get') else None

def wrap_request_putrequest(func, f_args, f_kwargs):
    self = safeindex(f_args, 0)
    if self:
        # self.__oboe_method = safeindex(f_args, 1) or safeget(f_kwargs, 'method')
        self.__oboe_path = safeindex(f_args, 2) or safeget(f_kwargs, 'url')
    return f_args, f_kwargs, {}

def wrap_request_endheaders(func, f_args, f_kwargs):
    if len(f_args) >= 1:
        self = f_args[0]
        self.putheader('X-Trace', oboe.last_id())
    return f_args, f_kwargs, {}

def wrap_request_getresponse(func, f_args, f_kwargs, res):
    kvs = { 'IsService': 'yes',
            'RemoteProtocol': 'http' }
    self = safeindex(f_args, 0)
    if self:
        kvs['RemoteHost'] = "%s:%s" % (getattr(self, 'host', ''), getattr(self, 'port', '80'))
        if hasattr(self, '__oboe_path'):
            kvs['ServiceArg'] = getattr(self, '__oboe_path') or '/'
            delattr(self, '__oboe_path')
    if hasattr(res, 'status'):
        kvs['HTTPStatus'] = getattr(res, 'status')
    edge_str = res.getheader('x-trace') if res and hasattr(res, 'getheader') else None
    return kvs, edge_str

HTTPLIB_LAYER = 'httplib'

def wrap(module):
    try:
        # Wrap putrequest.  This marks the beginning of the request, and is also
        # where
        wrapper_putrequest = oboe.log_method(HTTPLIB_LAYER,
                                before_callback=wrap_request_putrequest,
                                send_exit_event=False,
                                store_backtrace=oboe._collect_backtraces('httplib'))
        setattr(module.HTTPConnection, 'putrequest',
                wrapper_putrequest(module.HTTPConnection.putrequest))

        wrapper_endheaders = oboe.log_method(HTTPLIB_LAYER,
                                             before_callback=wrap_request_endheaders,
                                             send_entry_event=False,
                                             send_exit_event=False)
        setattr(module.HTTPConnection, 'endheaders',
                wrapper_endheaders(module.HTTPConnection.endheaders))

        wrapper_getresponse = oboe.log_method(HTTPLIB_LAYER,
                                              callback=wrap_request_getresponse,
                                              send_entry_event=False)
        setattr(module.HTTPConnection, 'getresponse',
                wrapper_getresponse(module.HTTPConnection.getresponse))
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)


try:
    import httplib
    wrap(httplib)
except ImportError, e:
    pass

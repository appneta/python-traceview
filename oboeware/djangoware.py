"""Tracelytics instrumentation for Django

 Copyright (C) 2011 by Tracelytics, Inc.
 All rights reserved.
"""

# django middleware for passing values to oboe
__all__ = ("OboeDjangoMiddleware", "install_oboe_instrumentation")

import oboe
from oboeware import imports
from oboeware import oninit
import sys, threading, functools

class OboeWSGIHandler(object):
    """ Wrapper WSGI Handler for Django's django.core.handlers.wsgi:WSGIHandler
    Can be used as a replacement for Django's WSGIHandler, e.g. with uWSGI.
    """
    def __init__(self):
        """ Import and instantiate django.core.handlers.WSGIHandler,
        now that the load_middleware wrapper below has been initialized. """
        from django.core.handlers.wsgi import WSGIHandler as djhandler
        self._handler = djhandler()

    def __call__(self, environ, start_response):
        return self._handler(environ, start_response)

# Middleware hooks listed here: http://docs.djangoproject.com/en/dev/ref/middleware/

class OboeDjangoMiddleware(object):

    def _singleline(self, e): # some logs like single-line errors better
        return str(e).replace('\n', ' ').replace('\r', ' ')

    def process_request(self, request):
        xtr_hdr = request.META.get("HTTP_X-Trace", request.META.get("HTTP_X_TRACE"))
        tracing_mode = oboe.config.get('tracing_mode')

        if not oboe.Context.isValid() and xtr_hdr and tracing_mode in ['always', 'through']:
            oboe.Context.fromString(xtr_hdr)

        try:
            if not oboe.Context.isValid():
                return
            if not oboe.Context.isValid() and tracing_mode == "always":
                oboe.start_trace('django')
            elif oboe.Context.isValid() and tracing_mode != 'never':
                oboe.log('django', 'entry')
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", self._singleline(e)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not oboe.Context.isValid():
            return
        try:
            kvs = {'Controller': view_func.__module__,
                   # XXX Not Python2.4-friendly
                   'Action': view_func.__name__ if hasattr(view_func, '__name__') else None}
            oboe.log('django', 'process_view', kvs=kvs)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", self._singleline(e)

    def process_response(self, request, response):
        if not oboe.Context.isValid():
            return response
        try:
            response['X-Trace'] = oboe.end_trace('django')
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", self._singleline(e)
        return response

    def process_exception(self, request, exception):
        try:
            oboe.log_exception()
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", self._singleline(e)

def middleware_hooks(module, objname):
    try:
        # wrap middleware callables we want to wrap
        cls = getattr(module, objname, None)
        if not cls:
            return
        for method in ['process_request',
                       'process_view',
                       'process_response',
                       'process_template_response',
                       'process_exception']:
            fn = getattr(cls, method, None)
            if not fn:
                continue
            profile_name = '%s.%s.%s' % (module.__name__, objname, method)
            setattr(cls, method,
                    oboe.profile_function(profile_name)(fn))
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

load_middleware_lock = threading.Lock()

def on_load_middleware():
    """ wrap Django middleware from a list """

    # protect middleware wrapping: only a single thread proceeds
    global load_middleware_lock         # lock gets overwritten as None after init
    if not load_middleware_lock:        # already initialized? abort
        return
    mwlock = load_middleware_lock
    mwlock.acquire()                    # acquire global lock
    if not load_middleware_lock:        # check again
        mwlock.release()                # abort
        return
    load_middleware_lock = None         # mark global as "init done"

    try:
        # middleware hooks
        from django.conf import settings
        for i in settings.MIDDLEWARE_CLASSES:
            if i.startswith('oboe'):
                continue
            dot = i.rfind('.')
            if dot < 0 or dot+1 == len(i):
                continue
            objname = i[dot+1:]
            imports.whenImported(i[:dot],
                                 functools.partial(middleware_hooks, objname=objname))  # XXX Not Python2.4-friendly

        # ORM
        if oboe.config['inst_enabled']['django_orm']:
            from oboeware import inst_django_orm
            imports.whenImported('django.db.backends', inst_django_orm.wrap)

        # load pluggaable instrumentation
        from loader import load_inst_modules
        load_inst_modules()

        # it's usually a tuple, but sometimes it's a list
        if type(settings.MIDDLEWARE_CLASSES) is tuple:
            settings.MIDDLEWARE_CLASSES = ('oboeware.djangoware.OboeDjangoMiddleware',) + settings.MIDDLEWARE_CLASSES
        elif type(settings.MIDDLEWARE_CLASSES) is list:
            settings.MIDDLEWARE_CLASSES = ['oboeware.djangoware.OboeDjangoMiddleware'] + settings.MIDDLEWARE_CLASSES
        else:
            print >> sys.stderr, "Oboe error: thought MIDDLEWARE_CLASSES would be either a tuple or a list, got " + \
                str(type(settings.MIDDLEWARE_CLASSES))

    finally: # release instrumentation lock
        mwlock.release()

def install_oboe_middleware(module):
    def base_handler_wrapper(func):
        @functools.wraps(func)  # XXX Not Python2.4-friendly
        def wrap_method(*f_args, **f_kwargs):
            on_load_middleware()
            return func(*f_args, **f_kwargs)
        return wrap_method

    try:
        cls = getattr(module, 'BaseHandler', None)
        try:
            if cls.OBOE_MIDDLEWARE_LOADER:
                return
        except Exception, e:
            cls.OBOE_MIDDLEWARE_LOADER = True
        fn = getattr(cls, 'load_middleware', None)
        setattr(cls, 'load_middleware', base_handler_wrapper(fn))
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

try:
    imports.whenImported('django.core.handlers.base', install_oboe_middleware)
    # phone home
    oninit.report_layer_init(layer='django')
except ImportError, e:
    # gracefully disable tracing if Tracelytics oboeware not present
    print >> sys.stderr, "[oboe] Unable to instrument app and middleware: %s" % e

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
from distutils.version import StrictVersion

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
    def __init__(self):
        from django.conf import settings
        try:
            self.layer = settings.OBOE_BASE_LAYER
        except AttributeError, e:
            self.layer = 'django'

    def _singleline(self, e): # some logs like single-line errors better
        return str(e).replace('\n', ' ').replace('\r', ' ')

    def process_request(self, request):
        try:
            xtr_hdr = request.META.get("HTTP_X-Trace",   request.META.get("HTTP_X_TRACE"))
            avw_hdr = request.META.get("HTTP_X-TV-Meta", request.META.get("HTTP_X_TV_META"))
            oboe.start_trace(self.layer, xtr=xtr_hdr, avw=avw_hdr, store_backtrace=False)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", self._singleline(e)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not oboe.Context.get_default().is_valid():
            return
        try:
            kvs = {'Controller': view_func.__module__,
                   # XXX Not Python2.4-friendly
                   'Action': view_func.__name__ if hasattr(view_func, '__name__') else None}
            oboe.log('process_view', None, keys=kvs, store_backtrace=False)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", self._singleline(e)

    def process_response(self, request, response):
        if not oboe.Context.get_default().is_valid():
            return response
        try:
            kvs = {'HTTP-Host': request.META['HTTP_HOST'],
                   'Method': request.META['REQUEST_METHOD'],
                   'URL': request.build_absolute_uri(),
                   'Status': response.status_code}
            response['X-Trace'] = oboe.end_trace(self.layer, keys=kvs)
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

def add_rum_template_tags():
    """ Register Django template tags.
        1. simple_tag uses method name, so make some proxy methods
        2. inserting into django.templates.libraries shortcut
        """
    def oboe_rum_header():
        return oboe.rum_header()
    def oboe_rum_footer():
        return oboe.rum_footer()

    import django.template as tem_mod

    l = tem_mod.Library()
    l.simple_tag(oboe_rum_header)
    l.simple_tag(oboe_rum_footer)
    tem_mod.libraries['oboe'] = l

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

        # templates
        if oboe.config['inst_enabled']['django_templates']:
            from oboeware import inst_django_templates
            import django
            if StrictVersion(django.get_version()) >= StrictVersion('1.3'):
                imports.whenImported('django.template.base', inst_django_templates.wrap)
            else:
                imports.whenImported('django.template', inst_django_templates.wrap)

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

    try:
        add_rum_template_tags()
    except Exception, e:
        print >> sys.stderr, "Oboe error: couldn't add RUM template tags: %s" % (e,)


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
            if not cls or cls.OBOE_MIDDLEWARE_LOADER:
                return
        except AttributeError, e:
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

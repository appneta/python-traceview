# Copyright (C) 2011 by Tracelytics, Inc.
# All rights reserved.


# django middleware for passing values to oboe
__all__ = ("OboeDjangoMiddleware", "install_oboe_instrumentation")

import sys

# Middleware hooks listed here: http://docs.djangoproject.com/en/dev/ref/middleware/

class OboeDjangoMiddleware(object):

    def __init__(self):
        try:
            import oboe
        except ImportError:
            print >> sys.stderr, "[oboeware] Can't import oboe, disabling OboeDjangoMiddleware"
            from django.core.exceptions import MiddlewareNotUsed
            raise MiddlewareNotUsed

    def _singleline(self, e): # some logs like single-line errors better
        return str(e).replace('\n', ' ').replace('\r', ' ')
    
    def process_request(self, request):
        import oboe
        xtr_hdr = request.META.get("HTTP_X-Trace", request.META.get("HTTP_X_TRACE"))
        tracing_mode = oboe.config.get('tracing_mode')

        if not oboe.Context.isValid() and xtr_hdr and tracing_mode in ['always', 'through']:
            oboe.Context.fromString(xtr_hdr)

        if not oboe.Context.isValid() and tracing_mode == "always":
            evt = oboe.Context.startTrace()
        elif oboe.Context.isValid() and tracing_mode != 'never':
            evt = oboe.Context.createEvent()

        if not oboe.Context.isValid(): return
        try:
            evt.addInfo('Layer', 'django')
            evt.addInfo('Label', 'entry')
            reporter = oboe.reporter().sendReport(evt)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", self._singleline(e)

    def process_view(self, request, view_func, view_args, view_kwargs):
        import oboe
        if not oboe.Context.isValid(): return
        try:
            evt = oboe.Context.createEvent()
            evt.addInfo('Layer', 'django')
            evt.addInfo('Label', 'process_view')
            evt.addInfo('Controller', view_func.__module__)
            evt.addInfo('Action', view_func.__name__ if hasattr(view_func, '__name__') else None)
            reporter = oboe.reporter().sendReport(evt)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", self._singleline(e)

    def process_response(self, request, response):
        import oboe
        if not oboe.Context.isValid(): return response
        try:
            evt = oboe.Context.createEvent()
            evt.addInfo('Layer', 'django')
            evt.addInfo('Label', 'exit')
            reporter = oboe.reporter().sendReport(evt)
            response['X-Trace'] = oboe.Context.toString()
            oboe.Context.clear()
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", self._singleline(e)
        return response

    def process_exception(self, request, exception):
        import oboe
        if not oboe.Context.isValid(): return
        try:
            evt = oboe.Context.createEvent()
            evt.addInfo('Layer', 'django')
            evt.addInfo('Label', 'error')
            evt.addInfo('ErrorMsg', str(exception))
            evt.addInfo('ErrorClass', exception.__class__.__name__)
            reporter = oboe.reporter().sendReport(evt)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", self._singleline(e)

def middleware_hooks(module, objname):
    import oboe
    try:
        # wrap middleware callables we want to wrap
        cls = getattr(module, objname, None)
        if not cls: return
        for method in ['process_request',
                       'process_view',
                       'process_response',
                       'process_template_response',
                       'process_exception']:
            fn = getattr(cls, method, None)
            if not fn: continue
            args = { 'layer': objname, # XXX ?
                     'store_return': False,
                     'Class': module.__name__ + '.' + objname,
                     'Function': method,
                     }
            setattr(cls, method, oboe.Context.log_method(**args)(fn))
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

        
def on_load_middleware():
    """ wrap Django middleware from a list """
    from django.conf import settings

    import functools, imports
    # middleware hooks
    for i in settings.MIDDLEWARE_CLASSES:
        if i.startswith('oboe'): continue
        dot = i.rfind('.')
        if dot < 0 or dot+1 == len(i): continue
        objname = i[dot+1:]
        imports.whenImported(i[:dot],
                             functools.partial(middleware_hooks, objname=objname))

    # ORM
    import inst_django_orm
    imports.whenImported('django.db.backends', inst_django_orm.wrap)

    import inst_memcache
    import inst_httplib2 

    # it's usually a tuple, but sometimes it's a list
    if type(settings.MIDDLEWARE_CLASSES) is tuple:
        settings.MIDDLEWARE_CLASSES = ('oboeware.djangoware.OboeDjangoMiddleware',) + settings.MIDDLEWARE_CLASSES
    elif type(settings.MIDDLEWARE_CLASSES) is list:     
        settings.MIDDLEWARE_CLASSES = ['oboeware.djangoware.OboeDjangoMiddleware'] + settings.MIDDLEWARE_CLASSES
    else:
        print >> sys.stderr, "Oboe error: thought MIDDLEWARE_CLASSES would be either a tuple or a list, got " + str(type(settings.MIDDLEWARE_CLASSES))

def install_oboe_middleware(module):
    from functools import wraps
    def base_handler_wrapper(func):
        @wraps(func)
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
    import imports as imports, functools
    imports.whenImported('django.core.handlers.base', install_oboe_middleware)
except ImportError, e:
    print >> sys.stderr, "[oboe] Unable to instrument app and middleware: %s" % e
    pass # gracefully disable tracing if Tracelytics oboeware not present

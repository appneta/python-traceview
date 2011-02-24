# django middleware for passing values to oboe
__all__ = ("OboeDjangoMiddleware", "wrap_middleware_classes")

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
            evt.addInfo('Agent', 'django')
            evt.addInfo('Label', 'entry')
            reporter = oboe.reporter().sendReport(evt)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", self._singleline(e)

    def process_view(self, request, view_func, view_args, view_kwargs):
        import oboe
        if not oboe.Context.isValid(): return
        try:
            evt = oboe.Context.createEvent()
            evt.addInfo('Agent', 'django')
            evt.addInfo('Label', 'process_view')
            evt.addInfo('Controller', view_func.__module__)
            evt.addInfo('Action', view_func.__name__)
            evt.addInfo('View-args', str(view_args))
            evt.addInfo('View-kwargs', str(view_kwargs))

            evt.addInfo('View-func', view_func.__name__)
            reporter = oboe.reporter().sendReport(evt)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", self._singleline(e)

    def process_response(self, request, response):
        import oboe
        if not oboe.Context.isValid(): return response
        try:
            evt = oboe.Context.createEvent()
            evt.addInfo('Agent', 'django')
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
            evt.addInfo('Agent', 'django')
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
            args = { 'agent': objname, # XXX ?
                     'store_return': False,
                     'Class': module.__name__ + '.' + objname,
                     'Function': method,
                     }
            #setattr(cls, method, wraphey(fn))
            setattr(cls, method, oboe.log_method(cls, **args)(fn))
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

def wrap_middleware_classes(mw_classes):
    """ wrap Django middleware from a list """
    import functools, imports
    for i in mw_classes:
        if i.startswith('oboe'): continue
        dot = i.rfind('.')
        if dot < 0 or dot+1 == len(i): continue
        objname = i[dot+1:]
        imports.whenImported(i[:dot],
                             functools.partial(middleware_hooks, objname=objname))

    return ('oboeware.django.OboeDjangoMiddleware',) + mw_classes 

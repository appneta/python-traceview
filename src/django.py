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

    def _singleline(self, s): # some logs like single-line errors better
        return str(e).replace('\n', ' ').replace('\r', ' ')
    
    def process_request(self, request):
        import oboe
        if not oboe.Context.isValid(): return
        try:
            evt = oboe.Context.createEvent()
            evt.addInfo('Agent', 'django')
            evt.addInfo('Label', 'process_request')
            reporter = oboe.reporter().sendReport(evt)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", _singleline(e)

    def process_view(self, request, view_func, view_args, view_kwargs):
        import oboe
        if not oboe.Context.isValid(): return
        try:
            evt = oboe.Context.createEvent()
            evt.addInfo('Agent', 'django:view')
            evt.addInfo('Label', 'entry')
            evt.addInfo('Controller', 'view')
            evt.addInfo('Action', view_func.__name__)
            evt.addInfo('View-args', str(view_args))
            evt.addInfo('View-kwargs', str(view_kwargs))
            reporter = oboe.reporter().sendReport(evt)
            request._oboe_log_view = True
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", _singleline(e)

    def process_response(self, request, response):
        import oboe
        if not oboe.Context.isValid() or not getattr(request, '_oboe_log_view', False): return response
        try:
            evt = oboe.Context.createEvent()
            evt.addInfo('Agent', 'django:view')
            evt.addInfo('Label', 'exit')
            reporter = oboe.reporter().sendReport(evt)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", _singleline(e)
        return response

    def process_exception(self, request, exception):
        import oboe
        if not oboe.Context.isValid(): return
        try:
            evt = oboe.Context.createEvent()
            evt.addInfo('Agent', 'django')
            evt.addInfo('Label', 'error')
            evt.addInfo('Message', str(exception))
            reporter = oboe.reporter().sendReport(evt)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", _singleline(e)

def middleware_hooks(module, objname):
    import oboe
    try:
        # wrap middleware callables we want to wrap
        cls = getattr(module, objname, None)
        if not cls: return
        for method in ['process_request',
                       'process_view',
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

    return mw_classes + ('oboeware.django.OboeDjangoMiddleware',)

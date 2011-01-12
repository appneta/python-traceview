# django middleware for passing values to oboe

__all__ = ("OboeDjangoMiddleware", )

# hooks listed here: http://docs.djangoproject.com/en/dev/ref/middleware/

class OboeDjangoMiddleware(object):
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        evt = Context.createEvent()
        evt.addInfo('Agent', 'django')
        evt.addInfo('Label', 'process_view')
        evt.addInfo('Controller', view_func.__name__)
        evt.addInfo('View-args', view_args)
        evt.addInfo('View-kwargs', view_kwargs)
        reporter = oboe.reporter().sendReport(evt)
        #request.environ['wsgiorg.routing_args'] = (view_args, view_kwargs.copy())
        #request.environ['wsgiorg.routing_args'] = ( view_args, dict(controller=view_func.__name__) )

    def process_exception(self, request, exception):
        evt = Context.createEvent()
        evt.addInfo('Agent', 'django')
        evt.addInfo('Label', 'error')
        evt.addInfo('Message', str(exception))
        reporter = oboe.reporter().sendReport(evt)

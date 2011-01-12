# django middleware for passing values to oboe

__all__ = ("OboeDjangoMiddleware", )

class OboeDjangoMiddlware(object):
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        #request.environ['wsgiorg.routing_args'] = (view_args, view_kwargs.copy())
        request.environ['wsgiorg.routing_args'] = ( view_args, dict(controller=view_func.__name__) )

    def process_exception(self, request, exception):
        evt = Context.createEvent()
        evt.addInfo('Agent', 'django')
        evt.addInfo('Label', 'error')
        evt.addInfo('Message', str(exception))
        reporter = oboe.reporter().sendReport(evt)

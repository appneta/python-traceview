# django middleware for passing values to oboe
__all__ = ("OboeDjangoMiddleware", )

import oboe

# Middleware hooks listed here: http://docs.djangoproject.com/en/dev/ref/middleware/

class OboeDjangoMiddleware(object):

    def _singleline(s): # some logs like single-line errors better
        return str(e).replace('\n', ' ').replace('\r', ' ')
    
    def process_request(self, request):
        if not oboe.Context.isValid(): return
        try:
            evt = oboe.Context.createEvent()
            evt.addInfo('Agent', 'wsgi')
            evt.addInfo('Label', 'process_request')
            evt.addInfo('Framework', 'Django')
            reporter = oboe.reporter().sendReport(evt)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", _singleline(e)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not oboe.Context.isValid(): return
        try:
            evt = oboe.Context.createEvent()
            evt.addInfo('Agent', 'wsgi')
            evt.addInfo('Label', 'process_view')
            evt.addInfo('Framework', 'Django')
            evt.addInfo('Controller', 'view')
            evt.addInfo('Action', view_func.__name__)
            evt.addInfo('View-args', str(view_args))
            evt.addInfo('View-kwargs', str(view_kwargs))
            reporter = oboe.reporter().sendReport(evt)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", _singleline(e)

    def process_exception(self, request, exception):
        if not oboe.Context.isValid(): return
        try:
            evt = oboe.Context.createEvent()
            evt.addInfo('Agent', 'wsgi')
            evt.addInfo('Label', 'error')
            evt.addInfo('Framework', 'Django')
            evt.addInfo('Message', str(exception))
            reporter = oboe.reporter().sendReport(evt)
        except Exception, e:
            print >> sys.stderr, "Oboe middleware error:", _singleline(e)

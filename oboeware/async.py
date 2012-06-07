# useful code for instrumenting asynchronous Python programs
# (c) 2011 Tracelytics, Inc.
import oboe

class OboeContextManager(object):
    """ A context manager (for the "with" statement) that sets and
        clears the context when entered, storing the metadata in an
        object passed by the constructor.  E.g.:

        with OboeContextManager(self.request):
            do_something()

        Here, any code called from do_something() will have its oboe
        context set from (and stored to, after finishing) the
        self.request object.
    """
    def __init__(self, ctxobj=None):
        """ stores oboe metadata as attribute of object 'ctxobj' """
        self.obj = ctxobj

    def __enter__(self):
        ctx = getattr(self.obj, '_oboe_md', None)
        if ctx:
            oboe.Context.set(ctx)
        elif oboe.Context.isValid():
            oboe.Context.clear()

    def __exit__(self, type, value, tb):
        if oboe.Context.isValid():
            ctx = oboe.Context.copy()
            setattr(self.obj, '_oboe_md', ctx)
            oboe.Context.clear()

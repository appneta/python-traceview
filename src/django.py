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
            setattr(cls, method, oboe.log_method(cls, **args)(fn))
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

def memcache_hooks(module):
    import oboe
    mc_methods = { 'get' : ['key'],
                  'set' : ['key'] }
    try:
        # wrap middleware callables we want to wrap
        cls = getattr(module, 'Client', None)
        if not cls: return
        for method in mc_methods.keys():
            fn = getattr(cls, method, None)
            if not fn:
                raise Exception('method %s not found in %s' % (method, module))
            args = { 'agent': 'memcache', # XXX ?
                     'store_return': False,
                     'Class': module.__name__ + '.Client',
                     'Function': method,
                     }
            setattr(cls, method, oboe.log_method(cls, **args)(fn))
            print >> sys.stderr, "Setting: ", method
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

OBOEWARE_HAS_BEEN_RUN=False

def install_oboe_instrumentation(mw_classes):
    """ wrap Django middleware from a list """
    global OBOEWARE_HAS_BEEN_RUN
    
    if OBOEWARE_HAS_BEEN_RUN:
        return

    import functools, imports
    # middleware hooks
    for i in mw_classes:
        if i.startswith('oboe'): continue
        dot = i.rfind('.')
        if dot < 0 or dot+1 == len(i): continue
        objname = i[dot+1:]
        imports.whenImported(i[:dot],
                             functools.partial(middleware_hooks, objname=objname))

    # ORM
    imports.whenImported('django.db.backends', db_module_wrap)

    # memcache
    print >> sys.stderr, "oboe init"
    imports.whenImported('memcache', functools.partial(memcache_hooks))

    mw_classes = ('oboeware.django.OboeDjangoMiddleware',) + mw_classes 
    OBOEWARE_HAS_BENN_RUN = True

    return mw_classes


class CursorOboeWrapper(object):
    def __init__(self, cursor, db):
        self.cursor = cursor
        self.db = db

    def execute(self, sql, params=()):
        import oboe
        import re
        kwargs = { 'Query' : sql }
        if 'NAME' in self.db.settings_dict:
            kwargs['Database'] = self.db.settings_dict['NAME']
        if 'HOST' in self.db.settings_dict:
            kwargs['RemoteHost'] = self.db.settings_dict['HOST']
        if 'ENGINE' in self.db.settings_dict:
            if re.search('postgresql', self.db.settings_dict['ENGINE']):
                kwargs['Flavor'] = 'postgresql'

        oboe.Context.log('djangoORM', 'entry', backtrace=True, **kwargs)
        try:
            return self.cursor.execute(sql, params)
        finally:
            oboe.Context.log('djangoORM', 'exit')
            
    def executemany(self, sql, param_list):
        import oboe
        import re
        kwargs = { 'Query' : sql }
        if 'NAME' in self.db.settings_dict:
            kwargs['Database'] = self.db.settings_dict['NAME']
        if 'HOST' in self.db.settings_dict:
            kwargs['RemoteHost'] = self.db.settings_dict['HOST']
        if 'ENGINE' in self.db.settings_dict:
            if re.search('postgresql', self.db.settings_dict['ENGINE']):
                kwargs['Flavor'] = 'postgresql'

        oboe.Context.log('djangoORM', 'entry', backtrace=True, **kwargs)
        try:
            return self.cursor.executemany(sql, param_list)
        finally:
            oboe.Context.log('djangoORM', 'exit')

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)

import sys

def db_module_wrap(module):
    try:
        cursor_method = module.BaseDatabaseWrapper.cursor

        def cursor_wrap(self):
            try:
                return CursorOboeWrapper(cursor_method(self), self)
            except Exception, e:
                print >> sys.stderr, "[oboe] Error in cursor_wrap", e

        setattr(module.BaseDatabaseWrapper, 'cursor', cursor_wrap)
    except Exception, e:
        print >> sys.stderr, "[oboe] Error in module_wrap", e

def cache_module_wrap(module):
    try:
        bc = module.BaseCache

        def cursor_wrap(self):
            try:
                return CursorOboeWrapper(cursor_method(self), self)
            except Exception, e:
                print >> sys.stderr, "[oboe] Error in cursor_wrap", e

        setattr(module.BaseCursorWrapper, 'cursor', cursor_wrap)
    except Exception, e:
        print >> sys.stderr, "[oboe] Error in module_wrap", e


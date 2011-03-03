# Copyright (C) 2011 by Tracelytics, Inc.
# All rights reserved.


import sys

def wrap(module):
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
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

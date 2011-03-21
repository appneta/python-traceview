# Copyright (C) 2011 by Tracelytics, Inc.
# All rights reserved.

import sys
from functools import partial

# memcache.Client methods (from docstring)
# Setup: __init__, set_servers, forget_dead_hosts, disconnect_all, debuglog
# Insertion: set, add, replace, set_multi
# Retrieval: get, get_multi
# Integers: incr, decr
# Removal: delete, delete_multi
# Mutate: append, cas, prepend

# memcache.Client setup
MC_SERVER_COMMANDS = set('__init__', 'set_servers')

# these methods also have the same names as Memcached commands/ops
MC_COMMANDS = set('get', 'get_multi',
                  'set', 'add', 'replace', 'set_multi',
                  'incr', 'decr',
                  'delete', 'delete_multi',
                  'append', 'cas', 'prepend')

def wrap_mc_method(funcname, func, f_args, f_kwargs, return_val):
    kvs = {}
    if funcname in MC_COMMANDS:
        kvs['KVOp'] = funcname
    # could examine f_args for key(s) here
    if funcname == 'get':
        kvs['KVHit'] = (return_val != None)
    return kvs

def wrap(module):
    import oboe
    try:
        # wrap middleware callables we want to wrap
        cls = getattr(module, 'Client', None)
        if not cls: return
        for method in MC_COMMANDS:
            fn = getattr(cls, method, None)
            if not fn:
                raise Exception('method %s not found in %s' % (method, module))
            args = { 'agent': 'memcache', # XXX ?
                     'store_return': False,
                     'callback': partial(wrap_mc_method, funcname=method),
                     'Class': module.__name__ + '.Client',
                     'Function': method,
                     }
            setattr(cls, method, oboe.log_method(cls, **args)(fn))
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

# Copyright (C) 2011 by Tracelytics, Inc.
# All rights reserved.

import sys
import oboe
import socket
from functools import partial

# memcache.Client methods (from docstring)
# Setup: __init__, set_servers, forget_dead_hosts, disconnect_all, debuglog
# Insertion: set, add, replace, set_multi
# Retrieval: get, get_multi
# Integers: incr, decr
# Removal: delete, delete_multi
# Mutate: append, cas, prepend

# memcache.Client setup
MC_SERVER_COMMANDS = set(('__init__', 'set_servers'))

# these methods also have the same names as Memcached commands/ops
MC_COMMANDS = set(('get', 'get_multi',
                   'set', 'add', 'replace', 'set_multi',
                   'incr', 'decr',
                   'delete', 'delete_multi',
                   'append', 'cas', 'prepend'))

MC_AGENT = 'memcache'

def wrap_mc_method(func, f_args, f_kwargs, return_val, funcname=None):
    kvs = {}
    if funcname in MC_COMMANDS:
        kvs['KVOp'] = funcname
    # could examine f_args for key(s) here
    if funcname == 'get':
        kvs['KVHit'] = int(return_val != None)
    return kvs

# peeks into internals
def wrap_get_server(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*f_args, **f_kwargs):
        ret = func(*f_args, **f_kwargs)
        try:
            args = {'KVKey' : f_args[1]}
            (host, _) = ret
            if host:
                if host.family == socket.AF_INET:
                    args['RemoteHost'] = host.ip
                elif host.family == socket.AF_UNIX:
                    args['RemoteHost'] = 'localhost'

            oboe.Context.log(MC_AGENT, 'info', **args)
        except Exception, e:
            print >> sys.stderr, "Oboe error: %s" % e
        finally:
            return ret
    return wrapper

def wrap(module):
    try:
        # wrap middleware callables we want to wrap
        cls = getattr(module, 'Client', None)
        if not cls: return
        for method in MC_COMMANDS:
            fn = getattr(cls, method, None)
            if not fn:
                raise Exception('method %s not found in %s' % (method, module))
            args = { 'agent': MC_AGENT,
                     'store_return': False,
                     'callback': partial(wrap_mc_method, funcname=method),
                     'Class': module.__name__ + '.Client',
                     'Function': method,
                     'backtrace': True,
                     }
            setattr(cls, method, oboe.log_method(cls, **args)(fn))

        # per-key memcache host hook
        fn = getattr(cls, '_get_server', None)
        setattr(cls, '_get_server', wrap_get_server(fn))
    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

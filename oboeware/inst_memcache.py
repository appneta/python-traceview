""" Tracelytics instrumentation for memcache client module.

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
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

MC_LAYER = 'memcache'

class DontCatchMe(Exception):
    pass

# pylint: disable-msg=W0613
def wrap_mc_method(func, f_args, f_kwargs, return_val, funcname=None):
    """Pulls the operation and (for get) whether a key was found, on each public method."""
    kvs = {}
    if funcname in MC_COMMANDS:
        kvs['KVOp'] = funcname
    # could examine f_args for key(s) here
    if funcname == 'get':
        kvs['KVHit'] = int(return_val != None)
    return kvs

def wrap_get_server(func):
    """ Wrapper for memcache._get_server, to read remote host on all ops.

    This relies on the module internals, and just sends an info event when this
    function is called.
    """
    from functools import wraps
    @wraps(func) # XXX Not Python2.4-friendly
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

            oboe.Context.log(MC_LAYER, 'info', **args)
        except Exception, e:
            print >> sys.stderr, "Oboe error: %s" % e
        return ret
    return wrapper

def dynamic_wrap(fn):
    def call_me(*args, **kwargs):
        return fn(*args, **kwargs)
    return call_me

def wrap(module):
    try:
        # wrap middleware callables we want to wrap
        cls = getattr(module, 'Client', None)
        if not cls:
            return
        for method in MC_COMMANDS:
            # delete_multi delegates to delete in pylibmc, so don't instrument it
            if method == 'delete_multi' and module.__name__ == 'pylibmc':
                continue
            fn = getattr(cls, method, None)
            if not fn:
                raise Exception('method %s not found in %s' % (method, module))
            args = { 'layer': MC_LAYER,
                     'store_return': False,
                     'callback': partial(wrap_mc_method, funcname=method), # XXX Not Python2.4-friendly
                     'Class': module.__name__ + '.Client',
                     'Function': method,
                     'backtrace': True,
                     }
            # print '%s.%s %s' % (module.__name__, method, fn)
            # XXX Not Python2.4-friendly
            wrapfn = fn.im_func if hasattr(fn, 'im_func') else dynamic_wrap(fn) # wrap unbound instance method
            setattr(cls, method, oboe.Context.log_method(**args)(wrapfn))

        # per-key memcache host hook
        if hasattr(cls, '_get_server'):
            fn = getattr(cls, '_get_server', None)
            setattr(cls, '_get_server', wrap_get_server(fn))

    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

for mod_name in ['memcache', 'pylibmc']:
    try:
        mod = __import__(mod_name)
        wrap(mod)
    except ImportError, ex:
        pass

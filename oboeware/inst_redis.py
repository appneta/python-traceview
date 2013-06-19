""" Tracelytics instrumentation for redis client module.

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
import sys
import oboe
import socket
from functools import partial, wraps

# these methods also have the same names as Memcached commands/ops
REDIS_COMMANDS = set(('get', 'get_multi',
                   'set', 'add', 'replace', 'set_multi',
                   'incr', 'decr',
                   'delete', 'delete_multi',
                   'append', 'cas', 'prepend', 'gets'))

def wrap_mc_method(func, f_args, f_kwargs, return_val, funcname=None):
    """Pulls the operation and (for get) whether a key was found, on each public method."""
    kvs = {}
    if funcname in MC_COMMANDS:
        kvs['KVOp'] = funcname
    # could examine f_args for key(s) here
    if funcname == 'get':
        kvs['KVHit'] = int(return_val != None)
    return kvs

def wrap_get_server(layer_name, func):
    """ Wrapper for memcache._get_server, to read remote host on all ops.

    This relies on the module internals, and just sends an info event when this
    function is called.
    """
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

            oboe.log('info', layer_name, keys=args)
        except Exception, e:
            print >> sys.stderr, "Oboe error: %s" % e
        return ret
    return wrapper

HITTABLE_COMMANDS = set(('GET','GETSET','HGET','LINDEX','LGET',
                        'RPOPLPUSH','LPOP','RPOP','BRPOPLPUSH',
                        'SPOP','SRANDMEMBER'))

def wrap_execute_command(func, f_args, f_kwargs, return_val):
    """ This is where most "normal" redis commands are instrumented. """
    kvs = {}
    kvs['KVOp'] = f_args[1]
    if f_args[1] in HITTABLE_COMMANDS:
        kvs['KVHit'] = return_val != None
    return kvs

def wrap_send_packed_command(layer_name, func):
    """ This is where we get the RemoteHost.

    This relies on the module internals, and just sends an info event when this
    function is called.
    """
    @wraps(func) # XXX Not Python2.4-friendly
    def wrapper(*f_args, **f_kwargs):
        ret = func(*f_args, **f_kwargs)
        try:
            conn_obj = f_args[0]
            if 'path' in dir(conn_obj):
                host = 'localhost'
            else:
                host = conn_obj.host + ':' + str(conn_obj.port)
            oboe.log('info', layer_name, keys={'RemoteHost': host})
        except Exception, e:
            print >> sys.stderr, "Oboe error: %s" % e
        return ret
    return wrapper

def wrap(layer_name, module):
    try:
        # first get the basic client methods; common point of processing is Client.execute_command
        cls = getattr(module, 'StrictRedis', None)
        if not cls:
            return
        execute_command = cls.execute_command
        wrapper = oboe.log_method(layer_name,
                                    callback=wrap_execute_command)
        setattr(cls, 'execute_command', wrapper(execute_command))

        # RemoteHost
        cls = getattr(module, 'Connection', None)
        if not cls:
            return
        wrapper = wrap_send_packed_command(layer_name, cls.send_packed_command)
        setattr(cls, 'send_packed_command', wrapper)

    except Exception, e:
        print >> sys.stderr, "Oboe error:", str(e)

try:
    import redis
    wrap('redis', redis)
except ImportError, ex:
    pass

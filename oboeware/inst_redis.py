""" Tracelytics instrumentation for redis client module.

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
import sys
import oboe
import socket
from functools import partial, wraps

HITTABLE_COMMANDS = set(('GET','GETSET','HGET','LINDEX','LGET',
                        'RPOPLPUSH','LPOP','RPOP','BRPOPLPUSH',
                        'SPOP','SRANDMEMBER'))

# TODO: add kvhit for mget
# PubSub has own execute_command

KEYABLE_COMMANDS = {'APPEND': 1,
                    'BITCOUNT': 1,
                    'BITOP': 2, #XXX DEST
                    'DECR': 1,
                    'EXISTS': 1,
                    'EXPIRE': 1,
                    'EXPIREAT': 1,
                    'GET': 1,
                    'GETBIT': 1,
                    'GETRANGE': 1,
                    'GETSET': 1,
                    'INCR': 1,
                    'INCRBY': 1,
                    'INCRBYFLOAT': 1,
                    'MOVE': 1,
                    'PEXPIRE': 1,
                    'PEXPIREAT': 1,
                    'PSETEX': 1,
                    'PTTL': 1,
                    'RENAME': 1,
                    'RENAMEX': 1,
                    'SET': 1,
                    'SETBIT': 1,
                    'SETEX': 1,
                    'SETNX': 1,
                    'SETRANGE': 1,
                    'STRLEN': 1,
                    'SUBSTR': 1,
                    'TTL': 1,
                    'TYPE': 1,

                    'LINDEX': 1,
                    'LINSERT': 1,
                    'LLEN': 1,
                    'LPOP': 1,
                    'LPUSH': 1,
                    'LPUSHX': 1,
                    'LRANGE': 1,
                    'LREM': 1,
                    'LSET': 1,
                    'LTRIM': 1,
                    'RPOP': 1,
                    'RPUSH': 1,
                    'RPOPLPUSH': 1,
                    'RPUSH': 1,
                    'RPUSHX': 1,
                    'SORT': 1,

                    'SADD': 1,
                    'SCARD': 1,
                    'SDIFF': 1,
                    'SDIFFSTORE': 1, #XXX DEST
                    'SINTERSTORE': 1, #XXX DEST
                    'SISMEMBER': 1,
                    'SMEMBERS': 1,
                    'SMOVE': 1,
                    'SPOP': 1,
                    'SRANDMEMBER': 1,
                    'SREM': 1,
                    'SUNIONSTORE': 1, #XXX DEST

                    'ZADD': 1,
                    'ZCARD': 1,
                    'ZCOUNT': 1,
                    'ZINCRBY': 1,
                    'ZINTERSTORE': 1, #XXX DEST
                    'ZRANGE': 1,
                    'ZRANGEBYSCORE': 1,
                    'ZRANK': 1,
                    'ZREM': 1,
                    'ZREMRANGEBYRANK': 1,
                    'ZREMRANGEBYSCORE': 1,
                    'ZREVRANGE': 1,
                    'ZREVRANGEBYSCORE': 1,
                    'ZREVRANK': 1,
                    'ZSCORE': 1,
                    'ZUNIONSCORE': 1, #XXX DEST

                    'HDEL': 1,
                    'HEXISTS': 1,
                    'HGET': 1,
                    'HGETALL': 1,
                    'HINCRBY': 1,
                    'HINCRBYFLOAT': 1,
                    'HKEYS': 1,
                    'HLEN': 1,
                    'HSET': 1,
                    'HSETNX': 1,
                    'HMSET': 1,
                    'HMGET': 1,
                    'HVALS': 1,

                    'PUBLISH': 1 # CHANNEL
                    }

SCRIPT_COMMANDS = { 'EVAL': 1, #SCRIPT
                    'EVALSHA': 1 #SHA
                  }

# these commands have two parts, as separate args in python redis client
# eg. SCRIPT LOAD
TWO_PARTERS = set(('SCRIPT','CLIENT','CONFIG','DEBUG'))


def wrap_execute_command(func, f_args, f_kwargs, return_val):
    """ This is where most "normal" redis commands are instrumented. """
    kvs = {}

    # command
    op = f_args[1]
    if op in TWO_PARTERS:
        op = op + ' ' + f_args[2]
    kvs['KVOp'] = op

    # key
    if op in KEYABLE_COMMANDS:
        kvs['KVKey'] = f_args[1+KEYABLE_COMMANDS[op]]

    # hit/miss
    if op in HITTABLE_COMMANDS:
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

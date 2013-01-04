""" Tracelytics instrumentation loader

Checks oboe.config['inst_enabled'] and imports as requested. used by middleware
and djangoware.

Copyright (C) 2012 by Tracelytics, Inc.
All rights reserved.
"""
import oboe

def _enabled(m):
    return oboe.config['inst_enabled'][m]

def load_inst_modules():
    if _enabled('memcache'):
        from oboeware import inst_memcache
    if _enabled('pymongo'):
        from oboeware import inst_pymongo
    if _enabled('sqlalchemy'):
        from oboeware import inst_sqlalchemy
    if _enabled('httplib'):
        from oboeware import inst_httplib
    # additionally, in djangoware.py: 'django_orm'

    import eventlet as e
    g = e.greenthread

    for (s, p) in [(g.spawn, 0), (g.spawn_n, 0), (g.spawn_after, 1), (g.spawn_after_local, 1)]:
        wrapped = oboe.log_method(None, spawn=True)(s)
        s = wrapped

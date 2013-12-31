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
    if _enabled('redis'):
        from oboeware import inst_redis
    # additionally, in djangoware.py: 'django_orm', 'django_templates'

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
    if _enabled('httplib2'):
        from oboeware import inst_httplib2
    if _enabled('memcache'):
        from oboeware import inst_memcache
    if _enabled('pymongo'):
        from oboeware import inst_pymongo
    if _enabled('sqlalchemy'):
        from oboeware import inst_sqlalchemy
    if _enabled('urllib3'):
        from oboeware import inst_urllib3

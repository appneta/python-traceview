""" Tracelytics instrumentation for SQLAlchemy.

 Copyright (C) 2011 by Tracelytics, Inc.
 All rights reserved.
"""
import oboe

DEFAULT_METHODS = ['do_execute', 'do_executemany', 'do_rollback', 'do_commit']
DIALECT_METHODS = ['do_rollback', 'do_commit']

# Mapping of method names to assumed SQL statements.
QUERY_MAP = {'do_rollback': 'ROLLBACK',
             'do_commit': 'COMMIT' }

def wrap_execute(func, f_args, _f_kwargs, _return_val):
    if func.__name__ in QUERY_MAP:
        return { 'Query': QUERY_MAP[func.__name__] }
    elif len(f_args) >= 3:
        return { 'Query': f_args[2].replace('%s', "''") }
    else:
        return {}

def wrap(module, class_name, methods):
    """ wrap default SQLAlchemy dialect, to catch execute calls to the cursor. """
    cls = getattr(module, class_name, None)
    decorate = oboe.log_method('sqlalchemy', backtrace=True, callback=wrap_execute)
    if cls:
        for method_name in methods:
            method = getattr(cls, method_name, None)
            if method:
                setattr(cls, method_name, decorate(method))

try:
    import sqlalchemy.engine.default as sad
    wrap(sad, 'DefaultDialect', DEFAULT_METHODS)
except ImportError, e:
    pass

try:
    import sqlalchemy.dialects.mysql.base as sdmb
    wrap(sdmb, 'MySQLDialect', DIALECT_METHODS)
except ImportError, e:
    pass

try:
    import sqlalchemy.dialects.postgresql.base as sdpb
    wrap(sdpb, 'PGDialect', DIALECT_METHODS)
except ImportError, e:
    pass

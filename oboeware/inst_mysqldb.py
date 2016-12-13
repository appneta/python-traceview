""" Tracelytics instrumentation for python-MySQLdb

 Copyright (C) 2014 AppNeta, Inc.
 All rights reserved.
"""
import oboe
import re

match = re.compile(r'''(?:[0-9\.]+)|'(?:[^'\\]|\\\')*?'|"(?:[^"\\]|\\\")*?"''')

def sanitized(query):
    return match.sub('?', query)

def wrap(module, cursors):
    """ wrap MySQLdb methods of interest """

    def wrap_do_query(func, f_args, _f_kwargs, _return_val):
        # TODO: can't figure out how to get Database name without state tracking
        db_conn = f_args[0]._get_db()
        remote_host = db_conn.get_host_info().split(' ')[0]
        query = f_args[1]

        if oboe.config.get('sanitize_sql', False):
            query = sanitized(f_args[1])

        return { 'RemoteHost': remote_host,
                 'Query': query }

    cls = getattr(cursors, 'BaseCursor', None)
    decorate = oboe.log_method('mysqldb',
                   store_backtrace=oboe._collect_backtraces('mysqldb'),
                   callback=wrap_do_query)
    if cls:
        # _do_query underlies both execute and executemany
        method = getattr(cls, '_do_query', None)
        if method:
            setattr(cls, '_do_query', decorate(method))
    else:
        print >> sys.stderr, "Oboe error: failed to find BaseCursor"


try:
    import MySQLdb as mdb_module
    import MySQLdb.cursors as mdb_cursors
    wrap(mdb_module, mdb_cursors)
except ImportError, e:
    pass

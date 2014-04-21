""" Tracelytics instrumentation for python-MySQLdb

 Copyright (C) 2014 AppNeta, Inc.
 All rights reserved.
"""
import oboe

def wrap_do_query(func, f_args, _f_kwargs, _return_val):
    # TODO: can't figure out how to get Database without state tracking
    return { 'RemoteHost': f_args[0]._get_db().get_host_info().split(' ')[0],
             'Query': f_args[1] }

def wrap(module, cursors):
    """ wrap MySQLdb methods of interest """
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

""" Tracelytics instrumentation for Django ORM.

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""

import oboe
import re
import sys

def wrap_execute(func, f_args, f_kwargs, res):
    obj, sql = f_args[:2]
    kwargs = {}
    log_sql_args = not oboe.config.get('sanitize_sql', False) and len(f_args) > 2
    if log_sql_args:
        kwargs['QueryArgs'] = str(f_args[2]).encode('utf-8')

    kwargs['Query'] = sql.encode('utf-8')
    if 'NAME' in obj.db.settings_dict:
        kwargs['Database'] = obj.db.settings_dict['NAME']
    if 'HOST' in obj.db.settings_dict:
        kwargs['RemoteHost'] = obj.db.settings_dict['HOST']
    if 'ENGINE' in obj.db.settings_dict:
        if re.search('post', obj.db.settings_dict['ENGINE']):
            kwargs['Flavor'] = 'postgresql'
        elif re.search('oracle', obj.db.settings_dict['ENGINE']):
            kwargs['Flavor'] = 'oracle'
    return kwargs

class CursorOboeWrapper(object):

    ###########################################################################
    # Django cursors can be wrapped arbitrarily deeply with the following API.
    # Each class contains a references to the DB object, and the next level
    # cursor. Control passes to the cursor in execute and executemany, wrapped
    # with whatever behavior the wrapper provides.
    ###########################################################################

    def __init__(self, cursor, db):
        self.cursor = cursor
        self.db = db

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __iter__(self):
        return iter(self.cursor)

    def execute(self, sql, params=()):
        return self.cursor.execute(sql, params)

    def executemany(self, sql, param_list):
        return self.cursor.executemany(sql, param_list)


def wrap(module):
    try:
        cursor_method = module.BaseDatabaseWrapper.cursor
        if getattr(cursor_method, '_oboe_wrapped', False):
            return

        oboe_wrapper = oboe.log_method('djangoORM', callback=wrap_execute,
                          store_backtrace=oboe._collect_backtraces('django_orm'))
        setattr(CursorOboeWrapper, 'execute', oboe_wrapper(CursorOboeWrapper.execute))
        setattr(CursorOboeWrapper, 'executemany', oboe_wrapper(CursorOboeWrapper.executemany))

        def cursor_wrap(self):
            try:
                return CursorOboeWrapper(cursor_method(self), self)
            except Exception, e:
                print >> sys.stderr, "[oboe] Error in cursor_wrap", e
                raise
        cursor_wrap._oboe_wrapped = True

        setattr(module.BaseDatabaseWrapper, 'cursor', cursor_wrap)
    except Exception, e:
        print >> sys.stderr, "[oboe] Error in module_wrap", e

# Copyright (C) 2011 by Tracelytics, Inc.
# All rights reserved.


import sys

class CursorOboeWrapper(object):
    def __init__(self, cursor, db):
        self.cursor = cursor
        self.db = db

    def execute(self, sql, params=()):
        import oboe
        import re
        kwargs = { 'Query' : sql }
        if 'NAME' in self.db.settings_dict:
            kwargs['Database'] = self.db.settings_dict['NAME']
        if 'HOST' in self.db.settings_dict:
            kwargs['RemoteHost'] = self.db.settings_dict['HOST']
        if 'ENGINE' in self.db.settings_dict:
            if re.search('postgresql', self.db.settings_dict['ENGINE']):
                kwargs['Flavor'] = 'postgresql'

        oboe.Context.log('djangoORM', 'entry', backtrace=True, **kwargs)
        try:
            return self.cursor.execute(sql, params)
        except Exception, e:
            oboe.Context.log('djangoORM', 'error', ErrorClass=e.__class__.__name__, Message=str(e))
            raise # reraise; finally still fires below
        finally:
            oboe.Context.log('djangoORM', 'exit')

    def executemany(self, sql, param_list):
        import oboe
        import re
        kwargs = { 'Query' : sql }
        if 'NAME' in self.db.settings_dict:
            kwargs['Database'] = self.db.settings_dict['NAME']
        if 'HOST' in self.db.settings_dict:
            kwargs['RemoteHost'] = self.db.settings_dict['HOST']
        if 'ENGINE' in self.db.settings_dict:
            if re.search('postgresql', self.db.settings_dict['ENGINE']):
                kwargs['Flavor'] = 'postgresql'

        oboe.Context.log('djangoORM', 'entry', backtrace=True, **kwargs)
        try:
            return self.cursor.executemany(sql, param_list)
        except Exception, e:
            oboe.Context.log('djangoORM', 'error', ErrorClass=e.__class__.__name__, Message=str(e))
            raise # reraise; finally still fires below
        finally:
            oboe.Context.log('djangoORM', 'exit')

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)

def wrap(module):
    try:
        cursor_method = module.BaseDatabaseWrapper.cursor
        if getattr(cursor_method, '_oboe_wrapped', False):
            return

        def cursor_wrap(self):
            try:
                return CursorOboeWrapper(cursor_method(self), self)
            except Exception, e:
                print >> sys.stderr, "[oboe] Error in cursor_wrap", e
        cursor_wrap._oboe_wrapped = True

        setattr(module.BaseDatabaseWrapper, 'cursor', cursor_wrap)
    except Exception, e:
        print >> sys.stderr, "[oboe] Error in module_wrap", e

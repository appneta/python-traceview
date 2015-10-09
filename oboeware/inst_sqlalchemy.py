""" Tracelytics instrumentation for SQLAlchemy.

 Copyright (C) 2011 by Tracelytics, Inc.
 All rights reserved.
"""
import oboe


def main():
    dialect_wrappers = {
        'do_commit': do_commit,
        'do_rollback': do_rollback
    }

    module_class_mappings = (
        ('sqlalchemy.engine.default', 'DefaultDialect', {
            'do_execute': do_execute,
            'do_executemany': do_execute,
            'do_commit': do_commit,
            'do_rollback': do_rollback
        },),
        ('sqlalchemy.dialects.mysql.base', 'MySQLDialect', dialect_wrappers,),
        ('sqlalchemy.dialects.postgresql.base', 'PGDialect', dialect_wrappers,),
    )

    for mod, cls, mappings in module_class_mappings:
        try:
            cls = getattr(__import__(mod, fromlist=[cls]), cls)
            wrap_methods(cls, mappings)
        except ImportError:
            pass


def do_execute(f, args, kwargs, ret):
    self, cursor, stmt, params = args[:4]
    info = {
        'Query': stmt,
        'RemoteHost': remotehost_from_connection(self, cursor.connection)
    }
    if not oboe.config.get('sanitize_sql', False):
        info['QueryArgs'] = str(params)
    return info


def do_commit(f, args, kwargs, ret):
    self, conn_fairy = args[:2]
    return {
        'Query': 'COMMIT',
        'RemoteHost': remotehost_from_connection(self, conn_fairy.connection)
    }


def do_rollback(f, args, kwargs, ret):
    self, conn_fairy = args[:2]
    dialect = self.dialect_description
    return {
        'Query': 'ROLLBACK',
        'RemoteHost': remotehost_from_connection(self, conn_fairy.connection)
    }


def remotehost_from_connection(dialect, conn):
    if dialect.dialect_description == 'mysql+mysqldb':
        return conn.get_host_info().split()[0].lower()


def wrap_methods(cls, mappings):
    for name, fn in mappings.items():
        base_method = getattr(cls, name)
        oboe_fn = oboe.log_method(
            'sqlalchemy',
            store_backtrace=oboe._collect_backtraces('sqlalchemy'),
            callback=fn)(base_method)
        setattr(cls, name, oboe_fn)


main()

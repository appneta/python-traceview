""" Tracelytics instrumentation for SQLAlchemy.

 Copyright (C) 2011 by Tracelytics, Inc.
 All rights reserved.
"""
import oboe


def main():
    default_wrappers = {
        'do_execute': do_execute_default,
        'do_executemany': do_execute_default,
        'do_commit': do_commit_default,
        'do_rollback': do_rollback_default
    }

    dialect_wrappers = {
        'do_commit': do_commit_dialect,
        'do_rollback': do_rollback_dialect
    }

    module_class_mappings = (
        ('sqlalchemy.engine.default', 'DefaultDialect', default_wrappers,),
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
        'RemoteHost': hostname_from_cursor(self, cursor)
    }
    if not oboe.config.get('sanitize_sql', False):
        info['QueryArgs'] = str(params)
    return info


def do_commit(f, args, kwargs, ret):
    self, conn_fairy = args[:2]
    return {
        'Query': 'COMMIT',
        'RemoteHost': hostname_from_connection_fairy(self, conn_fairy)
    }


def do_rollback(f, args, kwargs, ret):
    self, conn_fairy = args[:2]
    dialect = self.dialect_description
    return {
        'Query': 'ROLLBACK',
        'RemoteHost': hostname_from_connection_fairy(self, conn_fairy)
    }


do_execute_default  = do_execute
do_commit_default   = do_commit
do_rollback_default = do_rollback

do_commit_dialect   = do_commit
do_rollback_dialect = do_rollback


def hostname_from_connection_fairy(dialect, conn_fairy):
    dialect = dialect.dialect_description
    if dialect == 'mysql+mysqldb':
        return conn_fairy.connection.get_host_info().split()[0].lower()


def hostname_from_cursor(dialect, cursor):
    dialect = dialect.dialect_description
    if dialect == 'mysql+mysqldb':
        return cursor.connection.get_host_info().split()[0].lower()


def wrap_methods(cls, mappings):
    for name, fn in mappings.items():
        base_method = getattr(cls, name)
        oboe_fn = oboe.log_method(
            'sqlalchemy',
            store_backtrace=oboe._collect_backtraces('sqlalchemy'),
            callback=fn)(base_method)
        setattr(cls, name, oboe_fn)


main()

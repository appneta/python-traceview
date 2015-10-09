""" Tracelytics instrumentation for SQLAlchemy.

 Copyright (C) 2011 by Tracelytics, Inc.
 All rights reserved.
"""
import oboe


DIALECT_FLAVOR_NAMES = {
    'mysql+mysqldb': 'mysql'
}


def main():
    dialect_wrappers = {
        'do_commit': do_commit,
        'do_rollback': do_rollback
    }

    module_class_mappings = (
        ('sqlalchemy.engine.default', 'DefaultDialect', {
            'do_commit': do_commit,
            'do_execute': do_execute,
            'do_executemany': do_execute,
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


def wrap_methods(cls, mappings):
    for name, fn in mappings.items():
        base_method = getattr(cls, name)
        oboe_fn = oboe.log_method(
            'sqlalchemy',
            store_backtrace=oboe._collect_backtraces('sqlalchemy'),
            callback=fn)(base_method)
        setattr(cls, name, oboe_fn)


def do_commit(_f, args, _kwargs, _ret):
    self, conn_fairy = args[:2]
    flavor = DIALECT_FLAVOR_NAMES.get(self.dialect_description)
    return {
        'Flavor': flavor,
        'Query': 'COMMIT',
        'RemoteHost': remotehost_from_connection(flavor, conn_fairy.connection)
    }


def do_execute(_f, args, _kwargs, _ret):
    self, cursor, stmt, params = args[:4]
    flavor = DIALECT_FLAVOR_NAMES.get(self.dialect_description)
    info = {
        'Flavor': flavor,
        'Query': stmt,
        'RemoteHost': remotehost_from_connection(flavor, cursor.connection)
    }
    if not oboe.config.get('sanitize_sql', False):
        info['QueryArgs'] = str(params)
    return info


def do_rollback(_f, args, _kwargs, _ret):
    self, conn_fairy = args[:2]
    flavor = DIALECT_FLAVOR_NAMES.get(self.dialect_description)
    return {
        'Query': 'ROLLBACK',
        'RemoteHost': remotehost_from_connection(flavor, conn_fairy.connection)
    }


def remotehost_from_connection(flavor_name, conn):
    if flavor_name == 'mysql':
        return conn.get_host_info().split()[0].lower()


main()

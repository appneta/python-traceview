""" Tracelytics instrumentation for SQLAlchemy.

 Copyright (C) 2011 by Tracelytics, Inc.
 All rights reserved.
"""
import oboe


def main():
    dialect_wrappers = {
        'do_commit': do_commit_cb,
        'do_rollback': do_rollback_cb
    }

    module_class_mappings = (
        ('sqlalchemy.engine.default', 'DefaultDialect', {
            'do_commit': do_commit_cb,
            'do_execute': do_execute_cb,
            'do_executemany': do_execute_cb,
            'do_rollback': do_rollback_cb
        },),
        ('sqlalchemy.dialects.mysql.base', 'MySQLDialect', dialect_wrappers,),
        ('sqlalchemy.dialects.postgresql.base', 'PGDialect', dialect_wrappers,),
    )

    for mod, classname, mappings in module_class_mappings:
        try:
            cls = getattr(__import__(mod, fromlist=[classname]), classname)
        except (AttributeError, ImportError):
            pass
        else:
            wrap_methods(cls, mappings)


def wrap_methods(cls, mappings):
    for name, fn in mappings.items():
        try:
            base_method = getattr(cls, name)
        except AttributeError:
            log.warn('Failed to patch %s on %s', name, cls.__name__)
        else:
            oboe_fn = oboe.log_method(
                'sqlalchemy',
                store_backtrace=oboe._collect_backtraces('sqlalchemy'),
                callback=fn)(base_method)
            setattr(cls, name, oboe_fn)


def do_commit_cb(_f, args, _kwargs, _ret):
    self, conn = args[:2]
    return base_info(self.name, conn, 'COMMIT')


def do_execute_cb(_f, args, _kwargs, _ret):
    self, cursor, stmt, params = args[:4]
    info = base_info(self.name, cursor.connection, stmt)
    if not oboe.config.get('sanitize_sql', False):
        info['QueryArgs'] = str(params)
    return info


def do_rollback_cb(_f, args, _kwargs, _ret):
    self, conn = args[:2]
    return base_info(self.name, conn, 'ROLLBACK')


def base_info(dialect_name, conn, query):
    # This could be a real connection object, or a connection fairy (proxy)
    conn = getattr(conn, 'connection', conn)
    info = {
        'Flavor': dialect_name,
        'Query': query,
    }
    try:
        info['RemoteHost'] = remotehost_from_connection(dialect_name, conn)
    except:
        pass
    return info


def remotehost_from_connection(flavor_name, conn):
    if flavor_name == 'mysql':
        return conn.get_host_info().split()[0].lower()

    if flavor_name == 'postgresql':
        host_part = [part for part in conn.dsn.split()
                     if part.startswith('host=')]
        if host_part:
            return host_part[0].split('=')[1]


main()

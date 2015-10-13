"""Test SQLAlchemy instrumentation."""
from oboeware import inst_sqlalchemy

from . import base, trace_filters as filters


TEST_DB = 'test_inst_sqlalchemy'


class SqlAlchemyTest(base.TraceTestCase):
    def __init__(self, *args, **kwargs):
        super(SqlAlchemyTest, self).__init__(*args, **kwargs)
        self.lib = __import__('sqlalchemy')

    def assertSaneTrace(self):
        self.assertHasBaseEntryAndExit()
        self.assertEqual(1, len(self._last_trace.pop_events(
            filters.is_entry_event, filters.layer_is('sqlalchemy'))))
        exit = self._last_trace.pop_events(
            filters.is_exit_event, filters.layer_is('sqlalchemy'))
        self.assertEqual(1, len(exit))
        return exit[0]


class TestQueryAndArgs(SqlAlchemyTest):
    def test_simple(self):
        engine = self.lib.create_engine(mysql_tcp_dsn('mysql'))
        query = 'SELECT 1'

        with engine.connect() as conn:
            with self.new_trace():
                conn.execute(query)

        exit = self.assertSaneTrace()
        self.assertEqual(query, exit.props.get('Query'))
        self.assertEqual('()', exit.props.get('QueryArgs'))


    def test_args(self):
        engine = self.lib.create_engine(mysql_tcp_dsn('mysql'))
        query = 'SELECT 1 LIMIT %s'

        with engine.connect() as conn:
            with self.new_trace():
                conn.execute(query, 1)

        exit = self.assertSaneTrace()
        self.assertEqual(query, exit.props.get('Query'))
        self.assertEqual('(1,)', exit.props.get('QueryArgs'))

    # TODO refactor
    def test_commit(self):
        engine = self.lib.create_engine(mysql_tcp_dsn('mysql'))
        query = 'SELECT 1'

        with engine.connect() as conn:
            with self.new_trace():
                t = conn.begin()
                conn.execute(query)
                t.commit()

        self.assertHasBaseEntryAndExit()

        entries = self._last_trace.pop_events(
            filters.is_entry_event, filters.layer_is('sqlalchemy'))
        exits = self._last_trace.pop_events(
            filters.is_exit_event, filters.layer_is('sqlalchemy'))

        self.assertEqual(2, len(entries))
        self.assertEqual(2, len(exits))

        self.assertEqual(query, exits[0].props.get('Query'))
        self.assertEqual('COMMIT', exits[1].props.get('Query'))

    # TODO refactor
    def test_rollback(self):
        engine = self.lib.create_engine(mysql_tcp_dsn('mysql'))
        query = 'SELECT 1'

        with engine.connect() as conn:
            with self.new_trace():
                t = conn.begin()
                conn.execute(query)
                t.rollback()

        self.assertHasBaseEntryAndExit()

        entries = self._last_trace.pop_events(
            filters.is_entry_event, filters.layer_is('sqlalchemy'))
        exits = self._last_trace.pop_events(
            filters.is_exit_event, filters.layer_is('sqlalchemy'))

        self.assertEqual(2, len(entries))
        self.assertEqual(2, len(exits))

        self.assertEqual(query, exits[0].props.get('Query'))
        self.assertEqual('ROLLBACK', exits[1].props.get('Query'))


class TestRemoteHostAndFlavor(SqlAlchemyTest):
    def do_trace(self, engine):
        with engine.connect() as conn:
            with self.new_trace():
                conn.execute('SELECT 1')

    def test_mysql(self):
        engine = self.lib.create_engine(mysql_tcp_dsn('mysql'))
        self.do_trace(engine)
        exit = self.assertSaneTrace()
        self.assertEqual('127.0.0.1', exit.props.get('RemoteHost'))
        self.assertEqual('mysql', exit.props.get('Flavor'))

    def test_postgresql(self):
        engine = self.lib.create_engine(postgresql_tcp_dsn('', auth='postgres'))
        self.do_trace(engine)
        exit = self.assertSaneTrace()
        self.assertEqual('127.0.0.1', exit.props.get('RemoteHost'))
        self.assertEqual('postgresql', exit.props.get('Flavor'))

    def test_sqlite(self):
        engine = self.lib.create_engine('sqlite://')
        self.do_trace(engine)
        exit = self.assertSaneTrace()
        self.assertIsNone(exit.props.get('RemoteHost'))
        self.assertEqual('sqlite', exit.props.get('Flavor'))


def mysql_tcp_dsn(dbname, auth=None):
    return tcp_dsn('mysql+mysqldb', dbname, 3306, auth=auth)

def postgresql_tcp_dsn(dbname, auth=None):
    return tcp_dsn('postgresql+psycopg2', dbname, 5432, auth=auth)

def tcp_dsn(driver, dbname, port, auth=None):
    if auth:
        auth += '@'
    return '%s://%s127.0.0.1/%s?host=127.0.0.1?port=%d' % (driver, auth, dbname, port)

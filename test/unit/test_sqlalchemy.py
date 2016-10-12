"""Test SQLAlchemy instrumentation."""
from oboeware import inst_sqlalchemy

from . import base, trace_filters as filters


TEST_DSNS = (
    'sqlite://',
    'postgresql+psycopg2://postgres@127.0.0.1/?host=127.0.0.1?port=5432',
    'mysql+mysqldb://root@127.0.0.1/?host=127.0.0.1?port=3306',
    'mysql+pymysql://root@127.0.0.1/?host=127.0.0.1?port=3306',
)


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
        for dsn in TEST_DSNS:
            flavor = flavor_from_dsn(dsn)
            engine = self.lib.create_engine(dsn)
            query = 'SELECT 1'

            with engine.connect() as conn:
                with self.new_trace():
                    conn.execute(query)

            exit = self.assertSaneTrace()
            self.assertEqual(query, exit.props.get('Query'))

            # Either case is valid, don't expect a specific one, it may change
            self.assertIn(exit.props.get('QueryArgs'), ['{}','()'])


    def test_args(self):
        for dsn in TEST_DSNS:
            flavor = flavor_from_dsn(dsn)
            engine = self.lib.create_engine(dsn)

            if flavor == 'sqlite':
                query = 'SELECT 1 LIMIT ?'
            else:
                query = 'SELECT 1 LIMIT %s'

            with engine.connect() as conn:
                with self.new_trace():
                    conn.execute(query, 1)

            exit = self.assertSaneTrace()
            self.assertEqual(query, exit.props.get('Query'))
            self.assertEqual('(1,)', exit.props.get('QueryArgs'))


class TestTransaction(SqlAlchemyTest):
    def test_commit(self):
        for dsn in TEST_DSNS:
            exits = self.do_transaction(dsn, rollback=False)
            self.assertEqual('COMMIT', exits[1].props.get('Query'))

    def test_rollback(self):
        for dsn in TEST_DSNS:
            exits = self.do_transaction(dsn, rollback=True)
            self.assertEqual('ROLLBACK', exits[1].props.get('Query'))

    def do_transaction(self, dsn, rollback):
        engine = self.lib.create_engine(dsn)
        flavor = flavor_from_dsn(dsn)
        query = 'SELECT 1'

        with engine.connect() as conn:
            with self.new_trace():
                t = conn.begin()
                conn.execute(query)
                if rollback:
                    t.rollback()
                else:
                    t.commit()

        self.assertHasBaseEntryAndExit()

        entries = self._last_trace.pop_events(
            filters.is_entry_event, filters.layer_is('sqlalchemy'))
        exits = self._last_trace.pop_events(
            filters.is_exit_event, filters.layer_is('sqlalchemy'))

        # Postgres creates an extra event for ROLLBACK/COMMIT
        if flavor == 'postgresql':
            nevents = 3
        else:
            nevents = 2

        self.assertEqual(nevents, len(entries))
        self.assertEqual(nevents, len(exits))

        self.assertEqual(query, exits[0].props.get('Query'))
        return exits


class TestRemoteHostAndFlavor(SqlAlchemyTest):
    def test_simple(self):
        for dsn in TEST_DSNS:
            flavor = flavor_from_dsn(dsn)
            engine = self.lib.create_engine(dsn)
            with engine.connect() as conn:
                with self.new_trace():
                    conn.execute('SELECT 1')
            exit = self.assertSaneTrace()
            if flavor != 'sqlite':
                self.assertEqual('127.0.0.1', exit.props.get('RemoteHost'))
            self.assertEqual(flavor, exit.props.get('Flavor'))


def flavor_from_dsn(dsn):
    return dsn.split(':')[0].split('+')[0]

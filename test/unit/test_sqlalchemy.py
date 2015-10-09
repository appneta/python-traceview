"""Test SQLAlchemy instrumentation."""
from oboeware import inst_sqlalchemy

from . import base


TEST_DB = 'test_inst_sqlalchemy'


class TestWrappers(base.TraceTestCase):
    def __init__(self, *args, **kwargs):
        super(TestWrappers, self).__init__(*args, **kwargs)
        self.lib = __import__('sqlalchemy')

    def setUp(self):
        self.addCleanup(self.drop_db)
        self.create_db()

    def create_db(self):
        engine = self.lib.create_engine(tcp_dsn('mysql'))
        conn = engine.connect()
        conn.execute('CREATE DATABASE IF NOT EXISTS %s' % TEST_DB)
        conn.close()

        engine = self.lib.create_engine(tcp_dsn(TEST_DB))
        self.conn = engine.connect()
        self.addCleanup(self.conn.close)

        self.conn.execute('CREATE TABLE a (x INT)')

    def drop_db(self):
        engine = self.lib.create_engine(tcp_dsn('mysql'))
        conn = engine.connect()
        conn.execute('DROP DATABASE IF EXISTS %s' % TEST_DB)
        conn.close()

    def test_execute(self):
        self.conn.execute('SELECT x FROM a')


def tcp_dsn(dbname):
    return 'mysql+mysqldb://127.0.0.1/%s?host=127.0.0.1?port=3306' % dbname

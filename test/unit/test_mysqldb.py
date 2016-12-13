"""Test MySQLdb instrumentation"""

import base
import MySQLdb
from oboeware import inst_mysqldb # pylint: disable-msg=W0611
import os
import trace_filters as f
import unittest2 as unittest


MYSQL_HOST = os.environ.get('OBOE_MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('OBOE_MYSQL_USER', 'testuser')
MYSQL_PASS = os.environ.get('OBOE_MYSQL_PASS', None)
MYSQL_DB = os.environ.get('OBOE_MYSQL_DB', 'test_db')

is_mysqldb_layer = f.prop_is('Layer', 'mysqldb')

class TestMySQLdb(base.TraceTestCase):
    def __init__(self, *args, **kwargs):
        super(TestMySQLdb, self).__init__(*args, **kwargs)

    def _connect(self):
        return MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASS, db=MYSQL_DB)

    def assertIsQuery(self, **props):
        """ Checks for a basic Query span construct; any provided KV args will be
            checked for inclusion in exit event. """
        self.print_events()

        entry = self._last_trace.pop_events(f.is_entry_event, is_mysqldb_layer)
        self.assertEqual(1, len(entry))

        exit_props = [f.is_exit_event, is_mysqldb_layer]
        if props:
            for k,v in props.iteritems():
                exit_props.append(f.prop_is(k, v))

        exit = self._last_trace.pop_events(*exit_props)
        self.assertEqual(1, len(exit))

    def test_execute(self):
        """ Test cursor.execute() """
        import oboe
        oboe.config['sanitize_sql'] = False
        query = "select 1"
        with self.new_trace():
            db = self._connect()
            c = db.cursor()
            c.execute(query);
        self.assertIsQuery(Query=query, RemoteHost=MYSQL_HOST)

    def test_execute_sanitized(self):
        """ Test cursor.execute() with sanitization """
        import oboe
        oboe.config['sanitize_sql'] = True

        query = "select 1"
        reported_query = "select ?"

        with self.new_trace():
            db = self._connect()
            c = db.cursor()
            c.execute(query);
        self.assertIsQuery(Query=reported_query, RemoteHost=MYSQL_HOST)

    def test_executemany_and_errors(self):
        """ Test cursor.executemany(); also tests that errors work. """
        import oboe
        oboe.config['sanitize_sql'] = False
        query = """INSERT INTO breakfast (name, spam, eggs, sausage, price)
                  VALUES (%s, %s, %s, %s, %s)"""
        vals = [ ("Spam and Sausage Lover's Plate", '5', 1, 8, 7.95 ) ]

        with self.new_trace():
            db = self._connect()
            reported_query = query % tuple(db.literal(v) for v in vals[0])

            c = db.cursor()
            try:
                c.executemany(query, vals);
            except Exception, e:
                print e

        # query vals
        self.assertIsQuery(Query=reported_query, RemoteHost=MYSQL_HOST)

        # error: table 'breakfast' does not exist
        error = self._last_trace.pop_events(f.label_is('error'),
                                            f.prop_is('ErrorClass', 'ProgrammingError'))
        self.assertEqual(1, len(error))

    def test_executemany_and_errors_sanitized(self):
        """ Test cursor.executemany() with sanitizaiton of all arg types;
            also tests that errors work. """
        import oboe
        oboe.config['sanitize_sql'] = True
        query = """INSERT INTO breakfast (name, spam, eggs, sausage, price)
                  VALUES (%s, %s, %s, %s, %s)"""
        vals = [ ("Spam and Sausage Lover's Plate", '5', 1, 8, 7.95 ) ]
        reported_query = """INSERT INTO breakfast (name, spam, eggs, sausage, price)
                  VALUES (?, ?, ?, ?, ?)"""

        with self.new_trace():
            db = self._connect()

            c = db.cursor()
            try:
                c.executemany(query, vals);
            except Exception, e:
                print e

        # query vals
        self.assertIsQuery(Query=reported_query, RemoteHost=MYSQL_HOST)

        # error: table 'breakfast' does not exist
        error = self._last_trace.pop_events(f.label_is('error'),
                                            f.prop_is('ErrorClass', 'ProgrammingError'))
        self.assertEqual(1, len(error))


if __name__ == '__main__':
    unittest.main()

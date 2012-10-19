# Standalone script for testing server-side mongo 
import os
import oboe
import oboeware.inst_pymongo
from pymongo.connection import Connection
from pymongo.database import Database
from bson.dbref import DBRef
import time
import random

class MongoTest:

    def test_queries(self):
        oboe.start_trace("MongoTest")
        self._fake_mongo_query('db1', 'collection1',
                         'insert', '{"name":"MyName","type":"MyType","count":1,"info":{"x":203,"y":"102"}}'
                        )
        self._fake_mongo_command('db2', 'isMaster')
        self._fake_mongo_4sq('oauthaccesstoken', 'db.oauthaccesstoken.find({ "_id" : 0})')

        oboe.end_trace('MongoTest')

    def _fake_mongo_query(self, db, collection, queryop, query):
        """ simulates mongodb query """
        kvs = {
            'Flavor': 'mongodb',
            'Database': db,
            'Collection': collection,
            'QueryOp': queryop,
            'Query': query,
        } 
        oboe.log_entry('mongo', keys=kvs)
        time.sleep(1)
        oboe.log_exit('mongo', keys={})

    def _fake_mongo_command(self, db, command):
        """ simulates mongodb command """
        kvs = {
            'Flavor': 'mongodb',
            'Database': db,
            'QueryOp': 'command',
            'Query': '{}',
            'Command': command,
        } 
        oboe.log_entry('mongo', keys=kvs)
        time.sleep(1)
        oboe.log_exit('mongo', keys={})

    def _fake_mongo_4sq(self, collection, query):
        """ simulates mongodb query, as sent by foursquare """
        kvs = {
            'Flavor' : 'mongodb',
            'Collection' : collection,
            'Query' : query
        }
        oboe.log_entry('mongo', keys=kvs)
        time.sleep(1)
        oboe.log_exit('mongo', keys={})

def main():
    oboe.config['tracing_mode'] = 'always'
    oboe.config['sample_rate'] = 1.0

    MongoTest().test_queries()


if __name__ == '__main__':
    main()

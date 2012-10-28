# Standalone script for testing pymongo
import os
import oboe
import oboeware.inst_pymongo
from pymongo.connection import Connection
from pymongo.database import Database
from bson.dbref import DBRef
import time
import random

class MongoTest:

    def test1(self):
        db = Database(self._get_connection(), "pymongo_test")
        test = db.create_collection("test_1_4")
        test.save({"hello": u"world"})
        test.rename("test_1_new")
        db.drop_collection("test_1_new")

    def test2(self):
        db = Database(self._get_connection(), "pymongo_test")
        test = db.create_collection("test_2")
        try:
            for i in range(100):
                name = "test %d" % (i)
                ret = test.save({"name": name, "group_id" : i % 3, "posts": i % 20})
                print "Save Ret: %s" % (ret)

            ret = test.update({"posts": 10}, {"$set": {"posts": 100}}, multi=True, safe=True)
            #ret = test.update({"posts": 10}, {"$set": {"posts": 100}}, multi=True)
            print "Update Ret: %s" % (ret)
            test.update({"name": "test 2"}, {"$set": {"posts": 200}})
            test.create_index("posts")
            test.ensure_index("posts")

            for r in test.find({"posts":100}):
                print "Found: %s" % (r,)

            ret = test.remove({"posts": 1}, safe=True)
            print "Remove Ret: %s" % (ret)

            groups = test.group(
                key={"group_id":1},
                condition=None,
                initial={"post_sum":0},
                reduce="function(obj,prev) {prev.post_sum++;}"
            )
            for g in groups:
                print "Group: %s" % (g,)

            for d in test.distinct('posts'):
                print "Distinct: %s" % (d,)

            if 'reindex' in dir(test):
                test.reindex()
            test.drop_indexes()
        finally:
            db.drop_collection("test_2")


    def test3(self):
        db = Database(self._get_connection(), "pymongo_test")
        test = db.test2
        for r in test.find({"age": 10}):
            print r

    def test4(self):
        db = Database(self._get_connection(), "pymongo_test")
        test = db.create_collection("test_4")
        try:
            for i in range(5):
                name = "test %d" % (i)
                test.save({ "user_id": i, "name": name, "group_id" : i % 10, "posts": i % 20})

            test.create_index("user_id")
           
            for i in xrange(6):
                for r in test.find( { "group_id": random.randint(0,10) } ):
                    print "Found: %s " % (r)
         
        finally:
            db.drop_collection("test_4")


    # From https://gist.github.com/769687
    def dbref_test(self):
        db = Database(self._get_connection(), "pymongo_test")

        try:
            db.create_collection('owners')
            db.create_collection('tasks')

            # owners and tasks
            db.owners.insert({"name":"Jim"})
            db.tasks.insert([
                {"name": "read"},
                {"name": "sleep"}
                ])

            # update jim with tasks: reading and sleeping
            reading_task = db.tasks.find_one({"name": "read"})
            sleeping_task = db.tasks.find_one({"name": "sleep"})

            jim_update = db.owners.find_one({"name": "Jim"})
            jim_update["tasks"] = [
                DBRef(collection = "tasks", id = reading_task["_id"]),
                DBRef(collection = "tasks", id = sleeping_task["_id"])
                ]

            db.owners.save(jim_update)

            # get jim fresh again and display his tasks
            fresh_jim = db.owners.find_one({"name":"Jim"})
            print "tasks are:"
            for task in fresh_jim["tasks"]:
                print db.dereference(task)["name"]
        finally:
            db.drop_collection('owners')
            db.drop_collection('tasks')
        
    def _get_connection(self, *args, **kwargs):
        host = os.environ.get("MONGODB_HOST", "localhost")
        port = int(os.environ.get("MONGODB_PORT", 27017))
        return Connection(host, port, *args, **kwargs)

def main():
    oboe.config['tracing_mode'] = 'always'
    oboe.config['sample_rate'] = 1.0
    oboe.start_trace("MongoTest")

    mt = MongoTest()
    mt.test1()
    mt.test2()
    mt.test4()
    mt.dbref_test()

    oboe.end_trace('MongoTest')


if __name__ == '__main__':
    main()

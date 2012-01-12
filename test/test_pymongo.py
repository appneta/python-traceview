
import os
import oboe
import oboeware.inst_pymongo
from pymongo.connection import Connection
from pymongo.database import Database
import time
import random

class MongoTest:

    def test1(self):
        db = Database(self._get_connection(), "pymongo_test")
        test = db.create_collection("test_1")
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

            ret = test.update({"posts": 10}, {"$set": {"posts": 100}}, multi=True, safe=True)
            ret = test.update({"posts": 100}, {"$set": {"posts": 200}}, multi=True)
            test.update({"name": "test 2"}, {"$set": {"posts": 200}})
            test.create_index("posts")
            test.ensure_index("posts")

            for r in test.find({"posts":100}):
                print "Found: %s" % (r,)

            ret = test.remove({"posts": 1}, safe=True)

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

            test.reindex()
            test.drop_indexes()
        finally:
            db.drop_collection("test_2")


    def _get_connection(self, *args, **kwargs):
        host = os.environ.get("MONGODB_HOST", "localhost")
        port = int(os.environ.get("MONGODB_PORT", 27017))
        return Connection(host, port, *args, **kwargs)

def main():
    evt = oboe.Context.startTrace()
    evt.addInfo('Layer', 'MongoTest')
    evt.addInfo('Label', 'entry')
    oboe.reporter().sendReport(evt)

    mt = MongoTest()
    mt.test1()
    mt.test2()

    evt = oboe.Context.createEvent()
    evt.addInfo('Layer', 'MongoTest')
    evt.addInfo('Label', 'exit')
    oboe.reporter().sendReport(evt)


if __name__ == '__main__':
    main()

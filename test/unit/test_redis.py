""" Test redis client instrumentation. """

import base
import trace_filters as f
from oboeware import inst_redis # pylint: disable-msg=W0611
import unittest

# Filters for assertions re: inspecting Events in Traces
is_redis_layer = f.prop_is('Layer', 'redis')
is_redis_backtrace = f._and(f.has_prop('Backtrace'), is_redis_layer)


class TestRedis(base.TraceTestCase):
    def __init__(self, *args, **kwargs):
        self.lib = __import__('redis')
        super(TestRedis, self).__init__(*args, **kwargs)

    def setUp(self):
        self.client = self.lib.StrictRedis(host='127.0.0.1', port=6379, db=0)

    def tearDown(self):
        self.client = None

    def assertHasRedisCall(self, op, hit=None, key=None):
        self.assertEqual(1, len(self._last_trace.pop_events(f.is_entry_event, is_redis_layer)))
        preds = [f.is_exit_event, is_redis_layer, f.prop_is('KVOp', op)]
        if hit != None:
            preds.append(f.prop_is('KVHit', hit))
        if key != None:
            preds.append(f.prop_is('KVKey', key))
        exit_with_kvs = self._last_trace.pop_events(*preds)
        self.assertEqual(1, len(exit_with_kvs))

    def assertHasRemoteHost(self, num=1):
        self.assertEqual(num, len(self._last_trace.pop_events(f.is_remote_host_event)))
        return True

    def assertNoExtraEvents(self):
        self.assertEqual(0, len(self._last_trace.events()))

    def assertRedisTrace(self, op, num_remote_hosts=1, hit=None, key=None):
        self.assertHasBaseEntryAndExit()
        self.assertHasRedisCall(op, hit=hit, key=key)
        self.assertHasRemoteHost(num=num_remote_hosts)
        self.assertNoExtraEvents()

    ##### GET/SET/DELETE ######################################################

    def test_set(self):
        with self.new_trace():
            self.client.set('test1', 'set_val')
        self.assertRedisTrace(op='SET', key='test1')
        self.assertEqual('set_val', self.client.get('test1'))

    def test_get_hit(self):
        self.client.set('test1', 'get_val')
        with self.new_trace():
            ret = self.client.get('test1')
        self.assertRedisTrace(op='GET', hit=True, key='test1')
        self.assertEqual('get_val', ret)

    def test_get_miss(self):
        with self.new_trace():
            ret = self.client.get('test2')
        self.assertRedisTrace(op='GET', hit=False, key='test2')
        self.assertEqual(None, ret)

    def test_mget(self):
        kvs = {'key1': 'val1', 'key2': 'val2'}
        self.client.mset(kvs)
        self.client.delete('missing')
        with self.new_trace():
            ret = self.client.mget(kvs.keys(), 'missing')
        self.assertRedisTrace(op='MGET')
        self.assertEqual(ret, kvs.values() + [None])

    def test_mset(self):
        kvs = {'key1': 'val1', 'key2': 'val2'}
        with self.new_trace():
            self.client.mset(kvs)
        self.assertRedisTrace(op='MSET')
        self.assertEqual(kvs.values(), self.client.mget(kvs.keys()))

    def test_delete(self):
        self.client.set('test1', 'get_val')
        self.client.set('test2', 'get_val')
        with self.new_trace():
            ret = self.client.delete('test1','test2')
        self.assertRedisTrace(op='DEL')
        self.assertEqual(ret, 2)

    ##### TWO-WORD COMMANDS ###################################################
    # test a few of the two-word commands

    def test_client_list(self):
        with self.new_trace():
            ret = self.client.client_list()
        self.assertRedisTrace(op='CLIENT LIST')
        self.assertEqual(type(ret), list)
        self.assertEqual(type(ret[0]), dict)

    def test_script_exists(self):
        with self.new_trace():
            ret = self.client.script_exists('xxx')
        self.assertRedisTrace(op='SCRIPT EXISTS')
        self.assertEqual(ret, [False])

    ##### LIST COMMANDS #######################################################
    # test a few of the list commands

    def test_list_lpush(self):
        self.client.delete('listkey')
        with self.new_trace():
            ret = self.client.lpush('listkey','val')
        self.assertRedisTrace(op='LPUSH', key='listkey')
        self.assertEqual(ret, 1)

    def test_list_rpop(self):
        self.client.delete('listkey')
        ret = self.client.lpush('listkey','val')
        with self.new_trace():
            ret = self.client.rpop('listkey')
        self.assertRedisTrace(op='RPOP', key='listkey')
        self.assertEqual(ret, 'val')

    ##### HASH COMMANDS #######################################################
    # test a few of the hash commands

    def test_hset(self):
        self.client.delete('hashkey')
        with self.new_trace():
            ret = self.client.hset('hashkey', 'key', 'val')
        self.assertRedisTrace(op='HSET', key='hashkey')
        self.assertEqual(ret, 1)

    def test_hget_hit(self):
        self.client.delete('hashkey')
        ret = self.client.hset('hashkey', 'key', 'val')
        with self.new_trace():
            ret = self.client.hget('hashkey', 'key')
        self.assertRedisTrace(op='HGET', hit=True, key='hashkey')
        self.assertEqual(ret, 'val')

    def test_hget_miss(self):
        self.client.delete('hashkey')
        with self.new_trace():
            ret = self.client.hget('hashkey', 'key')
        self.assertRedisTrace(op='HGET', hit=False, key='hashkey')
        self.assertEqual(ret, None)

    ##### SET COMMANDS ########################################################
    # test a few of the set commands

    def test_set_sadd(self):
        self.client.delete('setkey')
        with self.new_trace():
            ret = self.client.sadd('setkey', 'item')
        self.assertRedisTrace(op='SADD', key='setkey')
        self.assertEqual(ret, 1)

    def test_set_srem(self):
        self.client.delete('setkey')
        self.client.sadd('setkey', 'item')
        with self.new_trace():
            ret = self.client.srem('setkey', 'item')
        self.assertRedisTrace(op='SREM', key='setkey')
        self.assertEqual(ret, 1)

    ##### SORTED SET COMMANDS #################################################
    # test a few of the z-set commands

    def test_set_zadd(self):
        self.client.delete('setkey')
        with self.new_trace():
            ret = self.client.zadd('setkey', 5, 'item')
        self.assertRedisTrace(op='ZADD', key='setkey')
        self.assertEqual(ret, 1)

    def test_set_srem(self):
        self.client.delete('setkey')
        self.client.zadd('setkey', 5, 'item')
        with self.new_trace():
            ret = self.client.zrem('setkey', 'item')
        self.assertRedisTrace(op='ZREM', key='setkey')
        self.assertEqual(ret, 1)

if __name__ == '__main__':
    unittest.main()

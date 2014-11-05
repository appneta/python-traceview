""" Test redis client instrumentation. """
from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import str

from . import base
from . import trace_filters as f
from oboeware import inst_redis # pylint: disable-msg=W0611
import unittest2 as unittest
from distutils.version import StrictVersion

# Filters for assertions re: inspecting Events in Traces
is_redis_layer = f.prop_is('Layer', 'redis')
is_redis_backtrace = f._and(f.has_prop('Backtrace'), is_redis_layer)


class TestRedis(base.TraceTestCase):
    def __init__(self, *args, **kwargs):
        self.lib = __import__('redis')
        self.lib_version = StrictVersion(self.lib.__version__)
        super(TestRedis, self).__init__(*args, **kwargs)

    def setUp(self):
        # use Redis class for versions < 2.4.10
        if not 'StrictRedis' in dir(self.lib):
            self.client = self.lib.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)
        else:
            self.client = self.lib.StrictRedis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

    def tearDown(self):
        self.client = None

    def assertHasRedisCall(self, **kvs):
        self.assertEqual(1, len(self._last_trace.pop_events(f.is_entry_event, is_redis_layer)))
        preds = [f.is_exit_event, is_redis_layer]
        for (k, v) in list(kvs.items()):
            preds.append(f.prop_is(k, v))
        exit_with_kvs = self._last_trace.pop_events(*preds)
        self.assertEqual(1, len(exit_with_kvs))

    def assertHasRemoteHost(self, num=1):
        self.assertEqual(num, len(self._last_trace.pop_events(f.is_remote_host_event)))

    def assertRedisTrace(self, num_remote_hosts=1, **kvs):
        self.assertHasBaseEntryAndExit()
        self.assertHasRedisCall(**kvs)
        self.assertHasRemoteHost(num=num_remote_hosts)
        self.assertNoExtraEvents()

    def guardServerFeature(self, command):
        import redis
        try:
            self.client.execute_command(command)
        except redis.client.ResponseError as e:
            if 'unknown command' in str(e):
                return self.skipTest("Installed version of Redis server doesn't support %s, skipping." % command)

    ##### GET/SET/DELETE ######################################################

    def test_set(self):
        with self.new_trace():
            self.client.set('test1', 'set_val')
        self.assertRedisTrace(KVOp='set', KVKey='test1')
        self.assertEqual('set_val', self.client.get('test1'))

    def test_get_hit(self):
        self.client.set('test1', 'get_val')
        with self.new_trace():
            ret = self.client.get('test1')
        self.assertRedisTrace(KVOp='get', KVHit=True, KVKey='test1')
        self.assertEqual('get_val', ret)

    def test_get_miss(self):
        with self.new_trace():
            ret = self.client.get('test2')
        self.assertRedisTrace(KVOp='get', KVHit=False, KVKey='test2')
        self.assertEqual(None, ret)

    def test_mget(self):
        kvs = {'key1': 'val1', 'key2': 'val2'}
        self.client.mset(kvs)
        self.client.delete('missing')
        with self.new_trace():
            ret = self.client.mget(list(kvs.keys()), 'missing')
        self.assertRedisTrace(KVOp='mget', KVKeyCount=3, KVHitCount=2)
        self.assertEqual(ret, list(kvs.values()) + [None])

    def test_mset(self):
        kvs = {'key1': 'val1', 'key2': 'val2'}
        with self.new_trace():
            self.client.mset(kvs)
        self.assertRedisTrace(KVOp='mset')
        self.assertEqual(list(kvs.values()), self.client.mget(list(kvs.keys())))

    def test_delete(self):
        self.client.set('test1', 'get_val')
        self.client.set('test2', 'get_val')
        with self.new_trace():
            ret = self.client.delete('test1','test2')
        self.assertRedisTrace(KVOp='del')
        if self.lib_version <= StrictVersion('2.7.4'):
            self.assertEqual(ret, True)
        else:
            self.assertEqual(ret, 2)

    ##### TWO-WORD COMMANDS ###################################################
    # test a few of the two-word commands

    def test_client_list(self):
        if not 'client_list' in dir(self.lib.Redis):
            self.skipTest('Version of library does not support client_list method.')
        self.guardServerFeature('client list')
        with self.new_trace():
            ret = self.client.client_list()
        self.assertRedisTrace(KVOp='client list')
        self.assertEqual(type(ret), list)
        self.assertEqual(type(ret[0]), dict)

    def test_script_exists(self):
        if not 'script_exists' in dir(self.lib.Redis):
            self.skipTest('Version of library does not support script_exists method.')
        self.guardServerFeature('script exists xxx')
        with self.new_trace():
            ret = self.client.script_exists('xxx')
        self.assertRedisTrace(KVOp='script exists')
        self.assertEqual(ret, [False])

    ##### LIST COMMANDS #######################################################
    # test a few of the list commands

    def test_list_lpush(self):
        self.client.delete('listkey')
        with self.new_trace():
            ret = self.client.lpush('listkey','val')
        self.assertRedisTrace(KVOp='lpush', KVKey='listkey')
        self.assertEqual(ret, 1)

    def test_list_rpop(self):
        self.client.delete('listkey')
        ret = self.client.lpush('listkey','val')
        with self.new_trace():
            ret = self.client.rpop('listkey')
        self.assertRedisTrace(KVOp='rpop', KVKey='listkey')
        self.assertEqual(ret, 'val')

    ##### HASH COMMANDS #######################################################
    # test a few of the hash commands

    def test_hset(self):
        self.client.delete('hashkey')
        with self.new_trace():
            ret = self.client.hset('hashkey', 'key', 'val')
        self.assertRedisTrace(KVOp='hset', KVKey='hashkey')
        self.assertEqual(ret, 1)

    def test_hget_hit(self):
        self.client.delete('hashkey')
        ret = self.client.hset('hashkey', 'key', 'val')
        with self.new_trace():
            ret = self.client.hget('hashkey', 'key')
        self.assertRedisTrace(KVOp='hget', KVHit=True, KVKey='hashkey')
        self.assertEqual(ret, 'val')

    def test_hget_miss(self):
        self.client.delete('hashkey')
        with self.new_trace():
            ret = self.client.hget('hashkey', 'key')
        self.assertRedisTrace(KVOp='hget', KVHit=False, KVKey='hashkey')
        self.assertEqual(ret, None)

    ##### SET COMMANDS ########################################################
    # test a few of the set commands

    def test_set_sadd(self):
        self.client.delete('setkey')
        with self.new_trace():
            ret = self.client.sadd('setkey', 'item')
        self.assertRedisTrace(KVOp='sadd', KVKey='setkey')
        self.assertEqual(ret, 1)

    def test_set_srem(self):
        self.client.delete('setkey')
        self.client.sadd('setkey', 'item')
        with self.new_trace():
            ret = self.client.srem('setkey', 'item')
        self.assertRedisTrace(KVOp='srem', KVKey='setkey')
        self.assertEqual(ret, 1)

    ##### SORTED SET COMMANDS #################################################
    # test a few of the z-set commands

    def test_zset_zadd(self):
        self.client.delete('setkey')
        with self.new_trace():
            if self.lib_version >= StrictVersion('2.4.10'):
                ret = self.client.zadd('setkey', 7, 'item')
            else:
                ret = self.client.zadd('setkey', 'item', 7)
        self.assertRedisTrace(KVOp='zadd', KVKey='setkey')
        self.assertEqual(ret, 1)

    def test_zset_srem(self):
        self.client.delete('setkey')

        if self.lib_version >= StrictVersion('2.4.10'):
            ret = self.client.zadd('setkey', 7, 'item')
        else:
            ret = self.client.zadd('setkey', 'item', 7)

        with self.new_trace():
            ret = self.client.zrem('setkey', 'item')
        self.assertRedisTrace(KVOp='zrem', KVKey='setkey')
        if self.lib_version <= StrictVersion('2.7.4'):
            self.assertEqual(ret, True)
        else:
            self.assertEqual(ret, 1)

    ##### PIPELINE COMMANDS ###################################################

    def test_transaction(self):
        """ Tests atomic transaction execution of pipeline. """
        self.client.delete('key1', 'hashkey1')
        p = self.client.pipeline()
        with self.new_trace():
            p.set('key1', 'val1').hset('hashkey1', 'key1', 'val1')
            ret = p.execute()
        # not sure what the exact cutoff should be here, but older versions have extra arguments
        if self.lib_version <= StrictVersion('2.7'):
            self.assertRedisTrace(KVOp='pipe:multi,set,hset,exec')
        else:
            self.assertRedisTrace(KVOp='pipe:set,hset')
        self.assertEqual(ret, [True, 1])

    def test_pipeline_and_fp(self):
        """ Tests non-atomic pipeline execution; also tests that fingerprint ops are ranked
            by frequency of occurrence in pipeline. """
        self.client.delete('key1', 'hashkey1')
        p = self.client.pipeline(transaction=False)
        with self.new_trace():
            p.set('key1', 'val1').hset('hashkey1', 'key1', 'val1').hset('hashkey1', 'key2', 'val2')
            ret = p.execute()
        self.assertRedisTrace(KVOp='pipe:hset,set')
        self.assertEqual(ret, [True, 1, 1])

    ##### PUBSUB COMMANDS #####################################################

    def test_subscribe(self):
        with self.new_trace():
            p = self.client.pubsub()
            p.subscribe('messages')
        self.assertRedisTrace(KVOp='subscribe')

    def test_psubscribe(self):
        with self.new_trace():
            p = self.client.pubsub()
            p.psubscribe('pattern')
        self.assertRedisTrace(KVOp='psubscribe')

    ##### SCRIPT COMMANDS #####################################################

    LUA_SCRIPT = """-- this is just meant to be longer than 100 chars
if redis.call("EXISTS",KEYS[1]) == 1 then
  return redis.call("INCR",KEYS[1])
else
  return nil
end
"""

    def test_eval(self):
        if not 'eval' in dir(self.lib.Redis):
            self.skipTest('Version of library does not support eval method.')
        self.guardServerFeature('EVAL')
        script = self.LUA_SCRIPT
        with self.new_trace():
            res = self.client.eval(script, 0, [])
        self.assertRedisTrace(KVOp='eval', Script=script[0:100])
        self.assertEquals(res, None)

if __name__ == '__main__':
    unittest.main()

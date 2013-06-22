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

    def assertRedisTrace(self, op, num_remote_hosts=1, hit=None, key=False):
        self.assertHasBaseEntryAndExit()
        self.assertHasRedisCall(op, hit=hit, key=key)
        self.assertHasRemoteHost(num=num_remote_hosts)
        self.assertNoExtraEvents()

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

if __name__ == '__main__':
    unittest.main()

""" Test redis client instrumentation. """

import base
from oboeware import inst_redis # pylint: disable-msg=W0611
import unittest

# Filters for assertions re: inspecting Events in Traces

def _and(*filters):
    def wrapped(*args, **kwargs):
        result = True
        for _filter in filters:
            result = result and _filter(*args, **kwargs)
        return result
    return wrapped
def has_prop(prop):
    return lambda ev: prop in ev.props
def prop_is_in(prop, values_set):
    return lambda ev: (prop in ev.props) and (ev.props[prop] in values_set)
def prop_is(prop, value):
    return lambda ev: (prop in ev.props) and (ev.props[prop] == value)
def label_is(label):
    return prop_is('Label', label)
def layer_is(layer):
    return prop_is('Layer', layer)
is_redis_layer = prop_is('Layer', 'redis')
is_redis_backtrace = _and(has_prop('Backtrace'), is_redis_layer)
is_remote_host_event = _and(has_prop('RemoteHost'), label_is('info'))
is_entry_event = label_is('entry')
is_exit_event = label_is('exit')


class TestRedis(base.TraceTestCase):
    def __init__(self, *args, **kwargs):
        self.lib = __import__('redis')
        super(TestRedis, self).__init__(*args, **kwargs)

    def setUp(self):
        self.client = self.lib.StrictRedis(host='127.0.0.1', port=6379, db=0)

    def tearDown(self):
        self.client = None

    def assertHasBaseEntryAndExit(self):
        self.print_events() # only prints anything if the following asserts will fail
        self.assertEqual(1, len(self._last_trace.pop_events(is_entry_event, layer_is('Python'))))
        self.assertEqual(1, len(self._last_trace.pop_events(is_exit_event, layer_is('Python'))))

    def assertHasRedisCall(self, op, hit=None):
        self.assertEqual(1, len(self._last_trace.pop_events(is_entry_event, is_redis_layer)))
        preds = [is_exit_event, is_redis_layer, prop_is('KVOp', op)]
        if hit != None:
            preds.append(prop_is('KVHit', hit))
        exit_with_kvs = self._last_trace.pop_events(*preds)
        self.assertEqual(1, len(exit_with_kvs))

    def assertHasRemoteHost(self, num=1):
        self.assertEqual(num, len(self._last_trace.pop_events(is_remote_host_event)))
        return True

    def assertNoExtraEvents(self):
        self.assertEqual(0, len(self._last_trace.events()))

    def assertRedisTrace(self, op, num_remote_hosts=1, hit=None):
        self.assertHasBaseEntryAndExit()
        self.assertHasRedisCall(op, hit=hit)
        self.assertHasRemoteHost(num=num_remote_hosts)
        self.assertNoExtraEvents()

    def test_set(self):
        with self.new_trace():
            self.client.set('test1', 'set')
        self.assertRedisTrace(op='SET')
        self.assertEqual('set', self.client.get('test1'))

    def test_get_hit(self):
        self.client.set('test1', 'get')
        with self.new_trace():
            ret = self.client.get('test1')
        self.assertRedisTrace(op='GET', hit=True)
        self.assertEqual('get', ret)

    def test_get_miss(self):
        with self.new_trace():
            ret = self.client.get('test2')
        self.assertRedisTrace(op='GET', hit=False)
        self.assertEqual(None, ret)

if __name__ == '__main__':
    unittest.main()

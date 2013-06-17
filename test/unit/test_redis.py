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

    def client(self):
        return self.lib.StrictRedis(host='127.0.0.1', port=6379, db=0)

    def assertHasEntryAndExit(self, op):
        self.assertEqual(1, len(self._last_trace.pop_events(is_entry_event, layer_is('Python'))))
        self.assertEqual(1, len(self._last_trace.pop_events(is_entry_event, is_redis_layer)))
        exit_with_kvop = self._last_trace.pop_events(is_exit_event, is_redis_layer, prop_is('KVOp', op))
        self.assertEqual(1, len(exit_with_kvop))
        self.assertEqual(1, len(self._last_trace.pop_events(is_exit_event, layer_is('Python'))))

    def assertHasRemoteHost(self, num=1):
        self.assertEqual(num, len(self._last_trace.pop_events(is_remote_host_event)))
        return True

    def assertNoExtraEvents(self):
        self.print_events() # only prints anything if the following assert will fail
        self.assertEqual(0, len(self._last_trace.events()))

    def assertSimpleTrace(self, op, num_remote_hosts=1):
        self.assertHasEntryAndExit(op)
        self.assertHasRemoteHost(num=num_remote_hosts)
        self.assertNoExtraEvents()

    def test_set(self):
        """ test set: client.set('key', 'value') """
        with self.new_trace():
            self.client().set('test1', '5')
        self.assertSimpleTrace(op='SET')

if __name__ == '__main__':
    unittest.main()

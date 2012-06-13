"""Test memcache client"""

import base
base.force_local_oboeware()
base.enable_mock_oboe()
from oboe.oboe_ext import OboeListener
import oboe
oboe.config['sample_rate'] = 1.0
oboe.config['tracing_mode'] = 'always'

import inst_memcache # pylint: disable-msg=W0611
import unittest

class Trace:
    def __init__(self):
        self.oboe = OboeListener()
        oboe._start_trace('Python')
    def __del__(self):
        oboe._end_trace('Python')
    def events(self, filter=None):
        return self.oboe.get_events(filter)
    def pop_events(self, filter=None):
        return self.oboe.pop_events(filter)

TEST_KEY = 'wqelihvwer'
TEST_VALUE = 'wclifun'
TEST_KEY_2 = 'sdfwefweew'
TEST_VALUE_2 = 'fewef333'
TEMP_TEST_KEY = 'fi24hfoihf'
TEMP_TEST_VALUE = 'oqwefhf'
TEMP_TEST_KEY_2 = 'ilufhweeewr'
TEMP_TEST_VALUE_2 = 'sdgsergerg'

class TestMemcacheMemcache(unittest.TestCase):
    moduleName = 'memcache'

    def __init__(self, *args, **kwargs):
        self.moduleName = self.__class__.moduleName
        self.lib = __import__(self.__class__.moduleName)
        super(TestMemcacheMemcache, self).__init__(*args, **kwargs)

    def setUp(self):
        self.client().set(TEST_KEY, TEST_VALUE)
        self.client().set(TEST_KEY_2, TEST_VALUE_2)

    def client(self):
        return self.lib.Client(["127.0.0.1:5679"])

    # def print_sigs(self, client):
    #     print '%10s: %s' % (self.moduleName, dir(client.set))
    #     print

    def print_events(self, events):
        print '\n'.join(['%s' % (ev.props) for ev in events])

    # def test_installation(self):
    #     """ test instrumentation installation """
    #     lib = __import__(self.moduleName)
    #     client = lib.Client(["127.0.0.1:5679"])
    #     #self.print_sigs(client)
    #     import inst_memcache
    #     #print
    #     #self.print_sigs(client)
    #     eventFilter = lambda x: 'Class' in x.props and x.props['Class'].startswith(self.moduleName)
    #     events = self.oboe.get_events(eventFilter=eventFilter)
    #     #print '\n'.join(['%10s: %s' % (ev.name, ev.props) for ev in events])
    #     self.assertEqual(13, len(events))

    def assertHasEntryAndExit(self, trace, op):
        backtraces = trace.pop_events(lambda ev: 'Backtrace' in ev.props)
        self.assertEqual(1, len(backtraces))
        self.assertEqual(backtraces[0].props['Function'], op)
        self.assertEqual(1, len(trace.pop_events(lambda ev: ev.props['Label'] == 'entry')))
        exits = trace.pop_events(lambda ev: ev.props['Label'] == 'exit' and 'KVOp' in ev.props)
        self.assertEqual(1, len(exits))
        self.assertEqual(exits[0].props['KVOp'], op)

    def assertHasRemoteHost(self, trace, num=1):
        # this is not supported in pylibmc
        supported_libs = set([ 'memcache' ])
        if self.moduleName in supported_libs:
            is_remote_host_event = lambda ev: 'RemoteHost' in ev.props and ev.props['Label'] == 'info'
            self.assertEqual(num, len(trace.pop_events(is_remote_host_event)))

    def assertNoExtraEvents(self, trace):
        self.assertEqual(0, len(trace.events()))

    def feature_supported_by(self, *supported_libs):
        if self.moduleName not in set(supported_libs):
            self.skipTest('feature not supported by %s' % self.moduleName)

    def test_set(self):
        """ test set: client.set('key', 'value') """
        trace = Trace()
        self.client().set('test1', '5')
        self.assertHasEntryAndExit(trace, op='set')
        self.assertHasRemoteHost(trace)
        self.assertNoExtraEvents(trace)

    def test_set_multi(self):
        """ test set_multi: client.set_multi({ 'key': 'value', 'key2': 'value2' }) """
        trace = Trace()
        self.client().set_multi({ 'key': 'value', 'key2': 'value2' })
        self.assertHasEntryAndExit(trace, op='set_multi')
        self.assertHasRemoteHost(trace, num=2)
        self.assertNoExtraEvents(trace)

    def test_setter(self):
        """ test setter: client['key'] = 'value' """
        self.feature_supported_by('pylibmc')
        trace = Trace()
        self.client()['test2'] = '5'
        self.assertHasEntryAndExit(trace, op='set')
        self.assertHasRemoteHost(trace)
        self.assertNoExtraEvents(trace)

    def test_get(self):
        """ test get: value = client.get('key') """
        trace = Trace()
        value = self.client().get(TEST_KEY)
        self.assertEqual(value, TEST_VALUE)
        self.assertHasEntryAndExit(trace, op='get')
        self.assertHasRemoteHost(trace)
        self.assertNoExtraEvents(trace)

    def test_get_multi(self):
        """ test get_multi: values = client.get_multi([ 'key', 'key2' ]) """
        trace = Trace()
        values = self.client().get_multi([ TEST_KEY, TEST_KEY_2 ])
        self.assertEquals(len(values), 2)
        self.assertHasEntryAndExit(trace, op='get_multi')
        self.assertHasRemoteHost(trace, num=2)
        self.assertNoExtraEvents(trace)

    def test_getter(self):
        """ test get: value = client['key'] """
        self.feature_supported_by('pylibmc')
        trace = Trace()
        value = self.client()[TEST_KEY]
        self.assertEqual(value, TEST_VALUE)
        self.assertHasEntryAndExit(trace, op='get')
        self.assertHasRemoteHost(trace)
        self.assertNoExtraEvents(trace)

    def test_delete(self):
        """ test delete: client.delete('key') """
        self.client().set(TEMP_TEST_KEY, TEMP_TEST_VALUE)
        trace = Trace()
        self.client().delete(TEMP_TEST_KEY)
        self.assertHasEntryAndExit(trace, op='delete')
        self.assertHasRemoteHost(trace)
        self.assertNoExtraEvents(trace)

    def test_delete_multi(self):
        """ test delete_multi: client.delete_multi([ 'key', 'key2' ]) """
        # this is not supported by pylibmc because delete_multi gets delegated to delete.
        self.feature_supported_by('memcache')
        self.client().set_multi({ TEMP_TEST_KEY: TEMP_TEST_VALUE, TEMP_TEST_KEY_2: TEMP_TEST_VALUE_2 })
        trace = Trace()
        self.client().delete_multi([ TEMP_TEST_KEY, TEMP_TEST_KEY_2 ])
        self.assertHasEntryAndExit(trace, op='delete_multi')
        self.assertHasRemoteHost(trace, num=2)
        self.assertNoExtraEvents(trace)

    def test_deleter(self):
        """ test deleter: del client['key'] """
        self.feature_supported_by('pylibmc')
        self.client().set(TEMP_TEST_KEY, TEMP_TEST_VALUE)
        trace = Trace()
        del self.client()[TEMP_TEST_KEY]
        self.assertHasEntryAndExit(trace, op='delete')
        self.assertHasRemoteHost(trace)
        self.assertNoExtraEvents(trace)

class TestMemcachePylibmc(TestMemcacheMemcache):
    moduleName = 'pylibmc'

if __name__ == '__main__':
    unittest.main()

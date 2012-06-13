"""Test memcache client"""

import base
base.force_local_oboeware()
base.enable_mock_oboe()
from oboe.oboe_ext import TestListener
import inst_memcache # pylint: disable-msg=W0611
import unittest

class TestMemcacheMemcache(unittest.TestCase):
    moduleName = 'memcache'

    def __init__(self, *args, **kwargs):
        self.moduleName = self.__class__.moduleName
        self.lib = __import__(self.__class__.moduleName)
        super(TestMemcacheMemcache, self).__init__(*args, **kwargs)

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

    def assertHasEntryAndExit(self, oboe):
        self.assertEqual(1, len(oboe.get_events(lambda ev: 'Backtrace' in ev.props and ev.props['Label'] == 'entry')))
        self.assertEqual(1, len(oboe.get_events(lambda ev: 'KVOp' in ev.props and ev.props['Label'] == 'exit')))
        return 2

    def assertHasRemoteHost(self, oboe):
        # this is not supported in pylibmc
        supported_libs = set([ 'memcache' ])
        if self.moduleName not in supported_libs:
            return 0
        self.assertEqual(1, len(oboe.get_events(lambda ev: 'RemoteHost' in ev.props and ev.props['Label'] == 'info')))
        return 1

    def feature_supported_by(self, *supported_libs):
        if self.moduleName not in set(supported_libs):
            self.skipTest('feature not supported by %s' % self.moduleName)

    def test_set(self):
        """ test set: c.set('key', 'value') """
        oboe = TestListener()
        self.client().set('test1', '5')
        num = self.assertHasEntryAndExit(oboe)
        num += self.assertHasRemoteHost(oboe)
        self.assertEqual(num, len(oboe.get_events()))

    def test_setter(self):
        """ test setter: c['key'] = 'value' """
        self.feature_supported_by('pylibmc')
        oboe = TestListener()
        self.client()['test2'] = '5'
        num = self.assertHasEntryAndExit(oboe)
        num += self.assertHasRemoteHost(oboe)
        self.assertEqual(num, len(oboe.get_events()))

    def test_get(self):
        """ test get: c.get('key') """
        oboe = TestListener()
        self.client().get('test3')
        num = self.assertHasEntryAndExit(oboe)
        num += self.assertHasRemoteHost(oboe)
        self.assertEqual(num, len(oboe.get_events()))

    def test_getter(self):
        """ test get: c.get('key') """
        self.feature_supported_by('pylibmc')
        TEST_VALUE = 'dsfsdfdsf'
        self.client()['test4'] = TEST_VALUE
        oboe = TestListener()
        value = self.client()['test4']
        self.assertEqual(value, TEST_VALUE)
        num = self.assertHasEntryAndExit(oboe)
        num += self.assertHasRemoteHost(oboe)
        self.assertEqual(num, len(oboe.get_events()))



class TestMemcachePylibmc(TestMemcacheMemcache):
    moduleName = 'pylibmc'

if __name__ == '__main__':
    unittest.main()

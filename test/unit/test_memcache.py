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

    def test_set(self):
        """ test set """
        oboe = TestListener()
        c = self.client()
        c.set('testset', '5')
        events = oboe.get_events()
        self.print_events(events)
        self.assertEqual(1, len(oboe.get_events(lambda ev: 'Backtrace' in ev.props and ev.props['Label'] == 'entry')))
        self.assertEqual(1, len(oboe.get_events(lambda ev: 'RemoteHost' in ev.props and ev.props['Label'] == 'info')))
        self.assertEqual(1, len(oboe.get_events(lambda ev: 'KVOp' in ev.props and ev.props['Label'] == 'exit')))
        self.assertEqual(3, len(events))

class TestMemcachePylibmc(TestMemcacheMemcache):
    moduleName = 'pylibmc'

if __name__ == '__main__':
    unittest.main()

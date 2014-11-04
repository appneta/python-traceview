"""Test memcache client"""
from __future__ import absolute_import

from . import base
from distutils.version import LooseVersion # pylint: disable-msg=W0611
from oboeware import inst_memcache # pylint: disable-msg=W0611
from . import trace_filters as f
import unittest2 as unittest


MODULE_NAMES = set([ 'memcache', 'pylibmc' ])
MC_HOSTS = ["127.0.0.1:11211"]

TEST_KEY = 'wqelihvwer'
TEST_VALUE = 'wclifun'
TEST_KEY_2 = 'sdfwefweew'
TEST_VALUE_2 = 'fewef333'
TEMP_TEST_KEY = 'fi24hfoihf'
TEMP_TEST_VALUE = 'oqwefhf'
TEMP_TEST_KEY_2 = 'ilufhweeewr'
TEMP_TEST_VALUE_2 = 'sdgsergerg'

# Filters for assertions re: inspecting Events in Traces
is_memcache_layer = f.prop_is_in('Layer', MODULE_NAMES)
is_memcache_backtrace = f._and(f.has_prop('Backtrace'), is_memcache_layer)


class TestMemcacheMemcache(base.TraceTestCase):
    """ This class contains tests not just for python-memcached
    but for other python memcache clients as well.  Other clients
    should inherit from this and set moduleName to their own
    module name.

    For anything that is not supported by a particular library,
    see the feature_supported_by method.

    """
    moduleName = 'memcache'

    def __init__(self, *args, **kwargs):
        self.moduleName = self.__class__.moduleName
        self.lib = __import__(self.__class__.moduleName)
        super(TestMemcacheMemcache, self).__init__(*args, **kwargs)

    def setUp(self):
        self.client().set(TEST_KEY, TEST_VALUE)
        self.client().set(TEST_KEY_2, TEST_VALUE_2)

    def client(self):
        return self.lib.Client(MC_HOSTS)

    def assertHasMemcacheEntryAndExit(self, op):
        self.assertHasBaseEntryAndExit()
        self.assertEqual(1, len(self._last_trace.pop_events(f.is_entry_event, is_memcache_layer)))
        exits = self._last_trace.pop_events(f.is_exit_event, is_memcache_layer, f.prop_is('KVOp', op))
        self.assertEqual(1, len(exits))

    def assertHasRemoteHost(self, num=1):
        # this is not supported in pylibmc
        supported_libs = set([ 'memcache' ])
        if self.moduleName in supported_libs:
            # if this fails: are you running a memached instance at MC_HOSTS?  if it can't
            # connect, this test will fail.
            self.assertEqual(num, len(self._last_trace.pop_events(f.is_remote_host_event)))

    def assertSimpleTrace(self, op, num_remote_hosts=1):
        self.assertHasMemcacheEntryAndExit(op)
        self.assertHasRemoteHost(num=num_remote_hosts)
        self.assertNoExtraEvents()

    def feature_supported_by(self, *supported_libs):
        """ Compare the version of the lib to the supported modules and versions
        passed in.  Skip the test if it's not supported. """
        supported = dict([m.split(' ', 1) if ' ' in m else (m, True) for m in supported_libs])
        support = supported[self.moduleName] if self.moduleName in supported else False
        if isinstance(support, str):
            op = support.split()[0]
            version = support.split()[1]
            support = eval('LooseVersion("%s") %s LooseVersion("%s")' % (self.lib.__version__, op, version))
        if not support:
            self.skipTest('feature not supported by %s v%s' % (self.moduleName, self.lib.__version__))

    def test_set(self):
        """ test set: client.set('key', 'value') """
        with self.new_trace():
            self.client().set('test1', '5')
        self.assertSimpleTrace(op='set')

    def test_set_multi(self):
        """ test set_multi: client.set_multi({ 'key': 'value', 'key2': 'value2' }) """
        with self.new_trace():
            self.client().set_multi({ 'key': 'value', 'key2': 'value2' })
        self.assertSimpleTrace(op='set_multi', num_remote_hosts=2)

    def test_setter(self):
        """ test setter: client['key'] = 'value' """
        self.feature_supported_by('pylibmc >= 1.2')
        with self.new_trace():
            self.client()['test2'] = '5'
        self.assertSimpleTrace(op='set')

    def test_get(self):
        """ test get: value = client.get('key') """
        with self.new_trace():
            value = self.client().get(TEST_KEY)
            self.assertEqual(value, TEST_VALUE)
        self.assertSimpleTrace(op='get')

    def test_get_multi(self):
        """ test get_multi: values = client.get_multi([ 'key', 'key2' ]) """
        with self.new_trace():
            values = self.client().get_multi([ TEST_KEY, TEST_KEY_2 ])
            self.assertEquals(len(values), 2)
        self.assertSimpleTrace(op='get_multi', num_remote_hosts=2)

    def test_getter(self):
        """ test get: value = client['key'] """
        self.feature_supported_by('pylibmc >= 1.2')
        with self.new_trace():
            value = self.client()[TEST_KEY]
            self.assertEqual(value, TEST_VALUE)
        self.assertSimpleTrace(op='get')

    def test_delete(self):
        """ test delete: client.delete('key') """
        self.client().set(TEMP_TEST_KEY, TEMP_TEST_VALUE)
        with self.new_trace():
            self.client().delete(TEMP_TEST_KEY)
        self.assertSimpleTrace(op='delete')

    def test_delete_multi(self):
        """ test delete_multi: client.delete_multi([ 'key', 'key2' ]) """
        # this is not supported by pylibmc because delete_multi gets delegated to delete.
        self.feature_supported_by('memcache')
        self.client().set_multi({ TEMP_TEST_KEY: TEMP_TEST_VALUE, TEMP_TEST_KEY_2: TEMP_TEST_VALUE_2 })
        with self.new_trace():
            self.client().delete_multi([ TEMP_TEST_KEY, TEMP_TEST_KEY_2 ])
        self.assertSimpleTrace(op='delete_multi', num_remote_hosts=2)

    def test_deleter(self):
        """ test deleter: del client['key'] """
        self.feature_supported_by('pylibmc >= 1.2')
        self.client().set(TEMP_TEST_KEY, TEMP_TEST_VALUE)
        with self.new_trace():
            del self.client()[TEMP_TEST_KEY]
        self.assertSimpleTrace(op='delete')

    def test_replace(self):
        """ test replace: client.replace('key', 'new_value') """
        self.client().set(TEMP_TEST_KEY, TEMP_TEST_VALUE)
        with self.new_trace():
            self.client().replace(TEMP_TEST_KEY, TEMP_TEST_VALUE_2)
        self.assertSimpleTrace(op='replace')

    def test_incr(self):
        """ test incr: client.incr('key') """
        self.client().set(TEMP_TEST_KEY, 3)
        with self.new_trace():
            value = self.client().incr(TEMP_TEST_KEY)
            self.assertEqual(4, value)
        self.assertSimpleTrace(op='incr')

    def test_decr(self):
        """ test decr: client.decr('key') """
        self.client().set(TEMP_TEST_KEY, 3)
        with self.new_trace():
            value = self.client().decr(TEMP_TEST_KEY)
            self.assertEqual(2, value)
        self.assertSimpleTrace(op='decr')

    def test_append(self):
        """ test append: client.append('key') """
        self.client().set(TEMP_TEST_KEY, TEMP_TEST_VALUE)
        with self.new_trace():
            self.client().append(TEMP_TEST_KEY, TEMP_TEST_VALUE_2)
        self.assertSimpleTrace(op='append')
        value = self.client().get(TEMP_TEST_KEY)
        self.assertEqual(value, TEMP_TEST_VALUE + TEMP_TEST_VALUE_2)

    def test_prepend(self):
        """ test prepend: client.prepend('key') """
        self.client().set(TEMP_TEST_KEY, TEMP_TEST_VALUE)
        with self.new_trace():
            self.client().prepend(TEMP_TEST_KEY, TEMP_TEST_VALUE_2)
        self.assertSimpleTrace(op='prepend')
        value = self.client().get(TEMP_TEST_KEY)
        self.assertEqual(value, TEMP_TEST_VALUE_2 + TEMP_TEST_VALUE)

    def test_cas(self):
        """ test gets and cas: value = client.gets('key'); result = client.cas('key', 'value') """
        # This is supported by pylibmc >= 1.2.0, too, but I think it might
        # require a newer version of libmemcached than I have, I think.  It
        # currently tells me "gets without cas behavior"
        self.feature_supported_by('memcache')
        self.client().set(TEMP_TEST_KEY, 1)
        with self.new_trace():
            value = self.client().gets(TEMP_TEST_KEY)
            self.assertEqual(1, value)
        self.assertSimpleTrace(op='gets')
        with self.new_trace():
            result = self.client().cas(TEMP_TEST_KEY, value + 1)
            self.assertEqual(True, result)
        self.assertSimpleTrace(op='cas', num_remote_hosts=2)
        value = self.client().get(TEMP_TEST_KEY)
        self.assertEqual(value, 2)

# memcache: http://www.tummy.com/Community/software/python-memcached/
# - originally developed by Evan Martin, later maintained by Sean Reifschneider

# pylibmc: http://pypi.python.org/pypi/pylibmc
# - authored by Ludvig Ericson

#class TestMemcachePylibmc(TestMemcacheMemcache):
#    moduleName = 'pylibmc'

# ## other libraries listed at http://code.google.com/p/memcached/wiki/Clients#Python
# python-libmemcached:
#   http://code.google.com/p/python-libmemcached/ author: davies.liu?
# cmemcache:
#   http://gijsbert.org/cmemcache/index.html author: Gijsbert de Haan
# django cache:
#   https://docs.djangoproject.com/en/dev/topics/cache/
# twisted memcache support:
#   http://twistedmatrix.com/documents/current/api/twisted.protocols.memcache.html


if __name__ == '__main__':
    unittest.main()

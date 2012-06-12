""" Test python-memcached library """

import unittest
from test_memcache_base import TestMemcacheBase

class TestMemcacheMemcache(unittest.TestCase, TestMemcacheBase):
    moduleName = 'memcache'
    def __init__(self, *args, **kwargs):
        super(TestMemcacheMemcache, self).__init__(*args, **kwargs)
        TestMemcacheBase.__init__(self, *args, **kwargs)

if __name__ == '__main__':
    unittest.main()

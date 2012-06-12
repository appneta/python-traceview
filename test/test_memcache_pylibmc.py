""" Test pylibmc library """

import unittest
from test_memcache_base import TestMemcacheBase

class TestMemcachePylibmc(unittest.TestCase, TestMemcacheBase):
    moduleName = 'pylibmc'
    def __init__(self, *args, **kwargs):
        super(TestMemcachePylibmc, self).__init__(*args, **kwargs)
        TestMemcacheBase.__init__(self, *args, **kwargs)

if __name__ == '__main__':
    unittest.main()

""" Tests for oboe/rum.py functionality. """
from __future__ import absolute_import

from . import base
import oboe
from oboe import rum
import unittest2 as unittest
import logging

class TestRUMDigest(base.TraceTestCase):
    def __init__(self, *args, **kwargs):
        super(TestRUMDigest, self).__init__(*args, **kwargs)

    def test_rum_digest(self):
        """ Tests the vailidity of the calculated RUM ID built using a known
        (and precalculated) user access key. """
        self.assertEqual(b'QPAY53rL1J6o-TaO_-5jZficI4Q=', rum._access_key_to_rum_id('f51e2a43-0ee5-4851-8a54-825773b3218e'))

if __name__ == '__main__':
    unittest.main()

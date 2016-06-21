""" Tests for oboe/oboe_ext.py Context functionality. """

import base
from oboe.oboe_ext import Context, Event, Metadata, UdpReporter
import unittest2 as unittest
import logging

class TestOnInit(base.TraceTestCase):
    def __init__(self, *args, **kwargs):
        super(TestOnInit, self).__init__(*args, **kwargs)

    def test_context(self):
        # Testing, 1 2 3...
        xtr = None
        url = 'some url'
        avw = None
        ctx = Context('test', '1234567890abcdef1234567890abcdef', 52, -1)
        data = ctx.should_trace(xtr or '', url or '', avw or '')

        # For now, just validate length. Eventually a parser
        # should be made to validate structure.
        self.assertEqual(len(data), 256)

if __name__ == '__main__':
    unittest.main()

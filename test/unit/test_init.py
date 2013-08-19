""" Tests for oboeware/oninit.py functionality. """

import base
from oboeware import oninit
import oboe
import unittest
import logging

class TestOnInit(base.TraceTestCase):
    def __init__(self, *args, **kwargs):
        super(TestOnInit, self).__init__(*args, **kwargs)

    def setUp(self):
        self.old_sample_rate = oboe.config['sample_rate']
        oboe.config['sample_rate'] = 0 # make sure we send init regardless of sampling

    def tearDown(self):
        oboe.config['sample_rate'] = self.old_sample_rate

    def assertInitTrace(self, layer='wsgi'):
        self.assertEqual(2, len(self._last_trace.events()))

    def test_report_layer_init(self):
        with self.new_trace(wrap_trace=False):
            oninit.report_layer_init(layer='Django')
        self.print_events()
        self.assertInitTrace()


if __name__ == '__main__':
    unittest.main()

""" Tests for oboeware/oninit.py functionality. """

import base
from oboeware import oninit
import oboe
import unittest2 as unittest
import logging

class TestOnInit(base.TraceTestCase):
    def __init__(self, *args, **kwargs):
        super(TestOnInit, self).__init__(*args, **kwargs)

    def setUp(self):
        self.old_sample_rate = oboe.config['sample_rate']
        oboe.config['sample_rate'] = 0 # make sure we send init regardless of sampling

    def tearDown(self):
        oboe.config['sample_rate'] = self.old_sample_rate

    def assertInitTrace(self, layer='wsgi', app_token=None):
        self.assertEqual(2, len(self._last_trace.events()))
        events = self._last_trace.events()

        # Validate base data
        entry = events[0].props
        self.assertEqual(entry['__Init'], 1)
        self.assertEqual(entry['Label'], 'entry')
        self.assertEqual(entry['Layer'], 'Django')
        self.assertEqual(entry['Language'], 'Python')

        # Validate versions
        self.assertEqual('Python.Version' in entry.keys(), True)
        self.assertEqual('Python.Oboe.Version' in entry.keys(), True)

        # Validate sample data
        self.assertEqual('_SP' in entry.keys(), True)

        # Validate app tokens
        self.assertEqual('App' in entry.keys(), True)
        if app_token:
            self.assertEqual(entry['AApp'], app_token)

        # Validate exit data
        exit = events[1].props
        self.assertEqual(exit['Label'], 'exit')
        self.assertEqual(exit['Layer'], 'Django')

    def test_report_layer_init(self):
        with self.new_trace(wrap_trace=False):
            oninit.report_layer_init(layer='Django')
        self.print_events()
        self.assertInitTrace()

        # Set a local app token and test again
        config = oboe.config
        app_token = '1234567890abcdef1234567890abcdef'
        config['app_token'] = app_token

        with self.new_trace(wrap_trace=False):
            oninit.report_layer_init(layer='Django')
        self.print_events()
        self.assertInitTrace(app_token=app_token)

        # Unset the local app token
        config['app_token'] = None

if __name__ == '__main__':
    unittest.main()

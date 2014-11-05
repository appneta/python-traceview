""" Base utilities for testing oboe python instrumentation

N.B. has on-import behavior to use repo-local oboe and set OBOE_TEST environment variable.
"""
from __future__ import print_function
from __future__ import absolute_import
from builtins import object
import os
import sys
from . import trace_filters as f
import unittest2 as unittest

def force_local_oboe():
    basepath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
    oboeware_path = os.path.join(basepath, 'oboeware')
    oboe_path = os.path.join(basepath)
    sys.path.insert(0, oboe_path)
    sys.path.insert(0, oboeware_path)


# dirty: using on import behaviors here, should be cleaned up
force_local_oboe()
os.environ['OBOE_TEST'] = '1'
import oboe
print(["Using oboe: %s" % (oboe.__path__,)], file=sys.stderr)
from oboe.oboe_test import OboeListener

class MockTrace(object):
    """ Mock trace.  Listens directly to events in mock oboe_ext. """
    def __init__(self, wrap_trace=True):
        self.listener = OboeListener()
        self.wrap_trace = wrap_trace
        if self.wrap_trace:
            oboe.start_trace('Python')
        self.ended = False

    def _end_trace(self):
        if not self.ended and self.wrap_trace:
            self.ended = True
            oboe.end_trace('Python')

    def __del__(self):
        self._end_trace()
        del self.listener

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._end_trace()

    def events(self, *filters):
        """ Returns all events matching the filters passed """
        return self.listener.get_events(*filters)

    def pop_events(self, *filters):
        """ Returns all events matching the filters passed,
        and also removes those events from the Trace so that
        they will not be returned by future calls to
        pop_events or events. """
        return self.listener.pop_events(*filters)

class TraceTestCase(unittest.TestCase):
    """ Base test case calss for oboeware unit tests. """
    def __init__(self, *args, **kwargs):
        self._last_trace = None
        super(TraceTestCase, self).__init__(*args, **kwargs)

    def new_trace(self, **kwargs):
        self._last_trace = MockTrace(**kwargs)
        return self._last_trace

    def print_events(self, *filters):
        for ev in self._last_trace.events(*filters):
            print('%s\n' % (ev.props))

    def assertHasBaseEntryAndExit(self):
        self.print_events() # only really prints anything if test case fails
        self.assertEqual(1, len(self._last_trace.pop_events(f.is_entry_event, f.layer_is('Python'))))
        self.assertEqual(1, len(self._last_trace.pop_events(f.is_exit_event, f.layer_is('Python'))))

    def assertNoExtraEvents(self):
        self.print_events() # only prints anything if the following assert will fail

""" Tests for exception string handling. """
from __future__ import absolute_import
from __future__ import unicode_literals

from . import base
from . import trace_filters as f
import oboe

class StringException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class TestLogExceptions(base.TraceTestCase):
    def __init__(self, *args, **kw):
        super(TestLogExceptions, self).__init__(*args, **kw)

    def test_unicode(self):
        """ Safely report an exception with a unicode message. """
        with self.new_trace():
            ucode = u'\xe4\xf6\xfc'
            try:
                raise StringException(ucode)
            except:
                oboe.log_exception()
        self.assertHasBaseEntryAndExit()
        # XXX possible desired API change: ErrorMsg not set as user might expect
        self.assertEqual(1, len(self._last_trace.pop_events(f.label_is('error'),
                                                            f.layer_is(None),
                                                            f.prop_is('ErrorClass', 'StringException'),
                                                            f.prop_is('ErrorMsg', '\xe4\xf6\xfc'))))
        self.assertNoExtraEvents()

    def test_log_method_exception(self):
        """ Be cool on instrumentation callback failure. """
        with self.new_trace():
            def bad_method(*args, **kwargs):
                raise Exception('boooo')

            @oboe.log_method('raiser', callback=bad_method)
            def raiser():
                pass

            raiser()
        self.assertHasBaseEntryAndExit()
        self.assertEqual(1, len(self._last_trace.pop_events(f.is_entry_event,
                                                            f.layer_is('raiser'))))
        self.assertEqual(1, len(self._last_trace.pop_events(f.is_exit_event,
                                                            f.layer_is('raiser'))))
        self.assertNoExtraEvents()

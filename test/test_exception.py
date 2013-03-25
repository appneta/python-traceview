import oboe
import unittest

class StringException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class TestLogExceptions(unittest.TestCase):
    def __init__(self, *args, **kw):
        super(TestLogExceptions, self).__init__(*args, **kw)

    def test_unicode(self):
        try:
            raise StringException(u'\xe4\xf6\xfc')
        except:
            oboe.log_exception()

    def test_log_method_exception(self):
        def bad_method(*args, **kwargs):
            raise Exception('boooo')

        @oboe.log_method('raiser', callback=bad_method)
        def raiser():
            pass

        raiser()

if __name__ == '__main__':
    oboe.config['tracing_mode'] = 'always'
    oboe.config['sample_rate'] = 1.0
    oboe.start_trace("ExceptionTest")

    unittest.main()

    oboe.end_trace("ExceptionTest")

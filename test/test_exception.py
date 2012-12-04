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

if __name__ == '__main__':
#    msg = str(u'\xe4\xf6\xfc')
    unittest.main()
        

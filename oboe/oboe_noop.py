""" Tracelytics instrumentation API for Python.

Copyright (C) 2012 by Tracelytics, Inc.
All rights reserved.

oboe_noop defines no-op classes for platforms we don't support building the c extension on
"""

# No-op classes intentionally left undocumented
# "Missing docstring"
# pylint: disable-msg=C0103

class Metadata(object):
    def __init__(self, _=None):
        pass

    @staticmethod
    def fromString(_):
        return Metadata()

    def createEvent(self):
        return Event()

    @staticmethod
    def makeRandom():
        return Metadata()

    def copy(self):
        return self

    def isValid(self):
        return False

    def toString(self):
        return ''

class Context(object):
    @staticmethod
    def init():
        pass

    @staticmethod
    def get_apptoken():
        return ''

    @staticmethod
    def get_apptoken_value():
        pass

    @staticmethod
    def get_apptoken_settings_value():
        pass

    @staticmethod
    def get_apptoken_counters_value():
        pass

    @staticmethod
    def setTracingMode(_):
        return False

    @staticmethod
    def setDefaultSampleRate(_):
        return False

    @staticmethod
    def sampleRequest(_, __, ___):
        return False

    @staticmethod
    def get():
        return Metadata()

    @staticmethod
    def set(_):
        pass

    @staticmethod
    def fromString(_):
        return Context()

    @staticmethod
    def copy():
        return Context()

    @staticmethod
    def clear():
        pass

    @staticmethod
    def isValid():
        return False

    @staticmethod
    def raw_send():
        pass

    @staticmethod
    def disconnect():
        pass

    @staticmethod
    def reconnect():
        pass

    @staticmethod
    def shutdown():
        pass

    @staticmethod
    def toString():
        return ''

    @staticmethod
    def createEvent():
        return Event()

    @staticmethod
    def startTrace(_=None):
        return Event()

    def __init__(self, layer, app_token, flags, sample_rate):
        pass

    def should_trace(self, xtr, url, avw):
        return 'test'


class Event(object):
    def __init__(self, _=None, __=None):
        pass

    def addInfo(self, _, __):
        pass

    def addEdge(self, _):
        pass

    def addEdgeStr(self, _):
        pass

    def getMetadata(self):
        return Metadata()

    def metadataString(self):
        return ''

    def send(self):
        pass

    def is_valid(self):
        return False

    @staticmethod
    def startTrace(_=None):
        return Event()

class Reporter(object):
    def __init__(self, _, __=None):
        pass

    def sendReport(self, _, __=None):
        pass

class UdpReporter(object):
    def __init__(self, _, __=None):
        pass

    def sendReport(self, _, __=None):
        pass

class FileReporter(object):
    def __init__(self, _, __=None):
        pass

    def sendReport(self, _, __=None):
        pass

class DebugLogger(object):
    def log(self, _):
        pass

class DebugLog(object):
    @staticmethod
    def getLevelName():
        pass

    @staticmethod
    def getModuleName():
        pass

    @staticmethod
    def getLevel():
        pass

    @staticmethod
    def setLevel():
        pass

    @staticmethod
    def setOutputStream():
        pass

    @staticmethod
    def setOutputFile():
        pass

    @staticmethod
    def addDebugLogger():
        pass

    @staticmethod
    def removeDebugLogger():
        pass

    @staticmethod
    def logMessage():
        pass

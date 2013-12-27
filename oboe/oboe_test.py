""" Tracelytics instrumentation API for Python.

Copyright (C) 2012 by Tracelytics, Inc.
All rights reserved.

oboe_noop defines no-op/test mock classes for:
a) platforms we don't support building the c extension on
b) running unit test
"""
listeners = []

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
        return True

    def toString(self):
        return ''

class Context(object):
    md = None

    @staticmethod
    def init():
        pass

    @staticmethod
    def setTracingMode(_):
        return False

    @staticmethod
    def setDefaultSampleRate(_):
        return False

    @staticmethod
    def sampleRequest(_, __, ___):
        return True

    @classmethod
    def get(cls):
        return cls.md

    @classmethod
    def set(cls, md):
        cls.md = md

    @staticmethod
    def fromString(_):
        return Context()

    @staticmethod
    def copy():
        return Context()

    @classmethod
    def clear(cls):
        cls.md = None

    @classmethod
    def isValid(cls):
        return cls.md != None

    @staticmethod
    def toString():
        return ''

    @staticmethod
    def createEvent():
        return Event()

    @staticmethod
    def startTrace(_=None):
        return Event()


class Event(object):
    def __init__(self, _=None, __=None):
        self.props = {}

    def addInfo(self, name, value):
        self.props[name] = value

    def addEdge(self, value):
        pass

    def addEdgeStr(self, _):
        pass

    def getMetadata(self):
        return Metadata()

    def metadataString(self):
        return ''

    def is_valid(self):
        return True

    @staticmethod
    def startTrace(_=None):
        return Event()

class UdpReporter(object):
    """ Mock UDP Reported; no-op for unsupported platforms, or unit test harness
        if in OBOE_TEST mode. """
    def __init__(self, _, __=None):
        pass

    def sendReport(self, event, __=None):
        for listener in listeners:
            listener.send(event)


class OboeListener(object):
    """ Simple test harness for intercepting event reports. """
    def __init__(self):
        self.events = []
        self.listeners = listeners
        listeners.append(self)

    def __del__(self):
        listeners.remove(self)

    def send(self, event):
        self.events.append(event)

    def get_events(self, *filters):
        """ Returns all events matching the filters passed """
        events = self.events
        for _filter in filters:
            events = [ev for ev in events if _filter(ev)]
        return events

    def pop_events(self, *filters):
        """ Returns all events matching the filters passed,
        and also removes those events from the Trace so that
        they will not be returned by future calls to
        pop_events or events. """
        matched = self.get_events(*filters)
        for match in matched:
            self.events.remove(match)
        return matched

    def __del__(self):
        self.listeners.remove(self)

""" This is a mock oboe_ext for use with instrumentation unit tests.  We force
this version to get added before the 'real' oboe_ext by doing a
sys.path.insert(0, ...) (see base.py), which is not nearly as elegant as
dependency injection but gets the job done. """

import os

listeners = []

from exceptions import NotImplementedError

class Context(object):
    def __init__(self):
        raise NotImplementedError

    @classmethod
    def clear(cls):
        cls.task_id = None

    @classmethod
    def copy(cls):
        raise NotImplementedError

    @classmethod
    def createEvent(cls):
        return Event()

    @classmethod
    def fromString(cls):
        raise NotImplementedError

    @classmethod
    def get(cls):
        raise NotImplementedError

    @classmethod
    def init(cls):
        cls.is_valid = True

    @classmethod
    def isValid(cls):
        return True

    @classmethod
    def set(cls):
        raise NotImplementedError

    @classmethod
    def startTrace(cls):
        cls.task_id = os.urandom(20)

    @classmethod
    def swigregister(cls):
        raise NotImplementedError

    @classmethod
    def toString(cls):
        raise NotImplementedError

class Event(object):
    def __init__(self):
        self.props = {}
    def __repr__(self):
        return 'Trace(%s)' % self.props
    def addInfo(self, name, value):
        self.props[name] = value
    def addEdge(self, *args):
        raise NotImplementedError
    def getMetadata(self):
        raise NotImplementedError
    def metadataString(self):
        raise NotImplementedError
    def startTrace(self):
        raise NotImplementedError

def Event_swigregister():
    raise NotImplementedError

class FileReporter(object):
    def __init__(self):
        raise NotImplementedError

def FileReporter_swigregister():
    raise NotImplementedError

class Metadata(object):
    def __init__(self):
        raise NotImplementedError

def Metadata_fromString():
    raise NotImplementedError

def Metadata_makeRandom():
    raise NotImplementedError

def Metadata_swigregister():
    raise NotImplementedError

class UdpReporter(object):
    def __init__(self, host, port):
        pass
    def sendReport(self, event):
        for listener in listeners:
            listener.send(event)

def UdpReporter_swigregister():
    raise NotImplementedError

# these are not really oboe pieces, but more a mock tracelyzer:

class OboeListener(object):
    def __init__(self):
        self.events = []
        self.listeners = listeners
        listeners.append(self)

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

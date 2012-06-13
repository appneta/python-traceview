""" This is a mock oboe_ext for use with instrumentation unit tests.  We force
this version to get added before the 'real' oboe_ext by doing a
sys.path.insert(0, ...) (see base.py), which is not nearly as elegant as
dependency injection but gets the job done. """

listeners = []

class Context:
    def __init__(self):
        raise Exception("Implement me!")

    @classmethod
    def clear(cls):
        raise Exception("Implement me!")

    @classmethod
    def copy(cls):
        raise Exception("Implement me!")

    @classmethod
    def createEvent(cls):
        return Event()

    @classmethod
    def fromString(cls):
        raise Exception("Implement me!")

    @classmethod
    def get(cls):
        raise Exception("Implement me!")

    @classmethod
    def init(cls):
        pass

    @classmethod
    def isValid(cls):
        return True

    @classmethod
    def set(cls):
        raise Exception("Implement me!")

    @classmethod
    def startTrace(cls):
        raise Exception("Implement me!")

    @classmethod
    def swigregister(cls):
        raise Exception("Implement me!")

    @classmethod
    def toString(cls):
        raise Exception("Implement me!")

class Event:
    def __init__(self):
        self.props = {}
    def addInfo(self, name, value):
        self.props[name] = value
    def addEdge(self, *args):
        raise Exception("Implement me!")
    def getMetadata(self):
        raise Exception("Implement me!")
    def metadataString(self):
        raise Exception("Implement me!")
    def startTrace(self):
        raise Exception("Implement me!")

def Event_swigregister():
    raise Exception("Implement me!")

class FileReporter:
    def __init__(self):
        raise Exception("Implement me!")

def FileReporter_swigregister():
    raise Exception("Implement me!")

class Metadata:
    def __init__(self):
        raise Exception("Implement me!")

def Metadata_fromString():
    raise Exception("Implement me!")

def Metadata_makeRandom():
    raise Exception("Implement me!")

def Metadata_swigregister():
    raise Exception("Implement me!")

class UdpReporter:
    def __init__(self, host, port):
        pass
    def sendReport(self, event):
        for listener in listeners:
            listener.send(event)

def UdpReporter_swigregister():
    raise Exception("Implement me!")

class TestListener(object):
    def __init__(self):
        self.events = []
        self.listeners = listeners
        listeners.append(self)

    def send(self, event):
        self.events.append(event)

    def get_events(self, eventFilter=None):
        return [ev for ev in self.events if eventFilter(ev)] if eventFilter else self.events

    def __del__(self):
        self.listeners.remove(self)

# This file was automatically generated by SWIG (http://www.swig.org).
# Version 2.0.11
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.





from sys import version_info
if version_info >= (2,6,0):
    def swig_import_helper():
        from os.path import dirname
        import imp
        fp = None
        try:
            fp, pathname, description = imp.find_module('_oboe_ext', [dirname(__file__)])
        except ImportError:
            import _oboe_ext
            return _oboe_ext
        if fp is not None:
            try:
                _mod = imp.load_module('_oboe_ext', fp, pathname, description)
            finally:
                fp.close()
            return _mod
    _oboe_ext = swig_import_helper()
    del swig_import_helper
else:
    import _oboe_ext
del version_info
try:
    _swig_property = property
except NameError:
    pass # Python < 2.2 doesn't have 'property'.
def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
    if (name == "thisown"): return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'SwigPyObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    if (not static):
        self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)

def _swig_setattr(self,class_type,name,value):
    return _swig_setattr_nondynamic(self,class_type,name,value,0)

def _swig_getattr(self,class_type,name):
    if (name == "thisown"): return self.this.own()
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError(name)

def _swig_repr(self):
    try: strthis = "proxy of " + self.this.__repr__()
    except: strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

try:
    _object = object
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0


class Metadata(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Metadata, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Metadata, name)
    __repr__ = _swig_repr
    def __init__(self, *args): 
        this = _oboe_ext.new_Metadata(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _oboe_ext.delete_Metadata
    __del__ = lambda self : None;
    __swig_getmethods__["fromString"] = lambda x: _oboe_ext.Metadata_fromString
    if _newclass:fromString = staticmethod(_oboe_ext.Metadata_fromString)
    def createEvent(self): return _oboe_ext.Metadata_createEvent(self)
    __swig_getmethods__["makeRandom"] = lambda x: _oboe_ext.Metadata_makeRandom
    if _newclass:makeRandom = staticmethod(_oboe_ext.Metadata_makeRandom)
    def copy(self): return _oboe_ext.Metadata_copy(self)
    def isValid(self): return _oboe_ext.Metadata_isValid(self)
    def toString(self): return _oboe_ext.Metadata_toString(self)
Metadata_swigregister = _oboe_ext.Metadata_swigregister
Metadata_swigregister(Metadata)

def Metadata_fromString(*args):
  return _oboe_ext.Metadata_fromString(*args)
Metadata_fromString = _oboe_ext.Metadata_fromString

def Metadata_makeRandom():
  return _oboe_ext.Metadata_makeRandom()
Metadata_makeRandom = _oboe_ext.Metadata_makeRandom

class Context(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Context, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Context, name)
    __repr__ = _swig_repr
    def __init__(self, *args): 
        this = _oboe_ext.new_Context(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _oboe_ext.delete_Context
    __del__ = lambda self : None;
    def should_trace(self, *args): return _oboe_ext.Context_should_trace(self, *args)
    __swig_getmethods__["get_apptoken"] = lambda x: _oboe_ext.Context_get_apptoken
    if _newclass:get_apptoken = staticmethod(_oboe_ext.Context_get_apptoken)
    __swig_getmethods__["get_apptoken_settings_value"] = lambda x: _oboe_ext.Context_get_apptoken_settings_value
    if _newclass:get_apptoken_settings_value = staticmethod(_oboe_ext.Context_get_apptoken_settings_value)
    __swig_getmethods__["get_apptoken_counters_value"] = lambda x: _oboe_ext.Context_get_apptoken_counters_value
    if _newclass:get_apptoken_counters_value = staticmethod(_oboe_ext.Context_get_apptoken_counters_value)
    __swig_getmethods__["get_apptoken_value"] = lambda x: _oboe_ext.Context_get_apptoken_value
    if _newclass:get_apptoken_value = staticmethod(_oboe_ext.Context_get_apptoken_value)
    __swig_getmethods__["setTracingMode"] = lambda x: _oboe_ext.Context_setTracingMode
    if _newclass:setTracingMode = staticmethod(_oboe_ext.Context_setTracingMode)
    __swig_getmethods__["setDefaultSampleRate"] = lambda x: _oboe_ext.Context_setDefaultSampleRate
    if _newclass:setDefaultSampleRate = staticmethod(_oboe_ext.Context_setDefaultSampleRate)
    __swig_getmethods__["sampleRequest"] = lambda x: _oboe_ext.Context_sampleRequest
    if _newclass:sampleRequest = staticmethod(_oboe_ext.Context_sampleRequest)
    __swig_getmethods__["get"] = lambda x: _oboe_ext.Context_get
    if _newclass:get = staticmethod(_oboe_ext.Context_get)
    __swig_getmethods__["toString"] = lambda x: _oboe_ext.Context_toString
    if _newclass:toString = staticmethod(_oboe_ext.Context_toString)
    __swig_getmethods__["set"] = lambda x: _oboe_ext.Context_set
    if _newclass:set = staticmethod(_oboe_ext.Context_set)
    __swig_getmethods__["fromString"] = lambda x: _oboe_ext.Context_fromString
    if _newclass:fromString = staticmethod(_oboe_ext.Context_fromString)
    __swig_getmethods__["copy"] = lambda x: _oboe_ext.Context_copy
    if _newclass:copy = staticmethod(_oboe_ext.Context_copy)
    __swig_getmethods__["clear"] = lambda x: _oboe_ext.Context_clear
    if _newclass:clear = staticmethod(_oboe_ext.Context_clear)
    __swig_getmethods__["isValid"] = lambda x: _oboe_ext.Context_isValid
    if _newclass:isValid = staticmethod(_oboe_ext.Context_isValid)
    __swig_getmethods__["init"] = lambda x: _oboe_ext.Context_init
    if _newclass:init = staticmethod(_oboe_ext.Context_init)
    __swig_getmethods__["raw_send"] = lambda x: _oboe_ext.Context_raw_send
    if _newclass:raw_send = staticmethod(_oboe_ext.Context_raw_send)
    __swig_getmethods__["disconnect"] = lambda x: _oboe_ext.Context_disconnect
    if _newclass:disconnect = staticmethod(_oboe_ext.Context_disconnect)
    __swig_getmethods__["reconnect"] = lambda x: _oboe_ext.Context_reconnect
    if _newclass:reconnect = staticmethod(_oboe_ext.Context_reconnect)
    __swig_getmethods__["shutdown"] = lambda x: _oboe_ext.Context_shutdown
    if _newclass:shutdown = staticmethod(_oboe_ext.Context_shutdown)
    __swig_getmethods__["createEvent"] = lambda x: _oboe_ext.Context_createEvent
    if _newclass:createEvent = staticmethod(_oboe_ext.Context_createEvent)
    __swig_getmethods__["startTrace"] = lambda x: _oboe_ext.Context_startTrace
    if _newclass:startTrace = staticmethod(_oboe_ext.Context_startTrace)
Context_swigregister = _oboe_ext.Context_swigregister
Context_swigregister(Context)

def Context_get_apptoken():
  return _oboe_ext.Context_get_apptoken()
Context_get_apptoken = _oboe_ext.Context_get_apptoken

def Context_get_apptoken_settings_value():
  return _oboe_ext.Context_get_apptoken_settings_value()
Context_get_apptoken_settings_value = _oboe_ext.Context_get_apptoken_settings_value

def Context_get_apptoken_counters_value():
  return _oboe_ext.Context_get_apptoken_counters_value()
Context_get_apptoken_counters_value = _oboe_ext.Context_get_apptoken_counters_value

def Context_get_apptoken_value():
  return _oboe_ext.Context_get_apptoken_value()
Context_get_apptoken_value = _oboe_ext.Context_get_apptoken_value

def Context_setTracingMode(*args):
  return _oboe_ext.Context_setTracingMode(*args)
Context_setTracingMode = _oboe_ext.Context_setTracingMode

def Context_setDefaultSampleRate(*args):
  return _oboe_ext.Context_setDefaultSampleRate(*args)
Context_setDefaultSampleRate = _oboe_ext.Context_setDefaultSampleRate

def Context_sampleRequest(*args):
  return _oboe_ext.Context_sampleRequest(*args)
Context_sampleRequest = _oboe_ext.Context_sampleRequest

def Context_get():
  return _oboe_ext.Context_get()
Context_get = _oboe_ext.Context_get

def Context_toString():
  return _oboe_ext.Context_toString()
Context_toString = _oboe_ext.Context_toString

def Context_set(*args):
  return _oboe_ext.Context_set(*args)
Context_set = _oboe_ext.Context_set

def Context_fromString(*args):
  return _oboe_ext.Context_fromString(*args)
Context_fromString = _oboe_ext.Context_fromString

def Context_copy():
  return _oboe_ext.Context_copy()
Context_copy = _oboe_ext.Context_copy

def Context_clear():
  return _oboe_ext.Context_clear()
Context_clear = _oboe_ext.Context_clear

def Context_isValid():
  return _oboe_ext.Context_isValid()
Context_isValid = _oboe_ext.Context_isValid

def Context_init():
  return _oboe_ext.Context_init()
Context_init = _oboe_ext.Context_init

def Context_raw_send(*args):
  return _oboe_ext.Context_raw_send(*args)
Context_raw_send = _oboe_ext.Context_raw_send

def Context_disconnect(*args):
  return _oboe_ext.Context_disconnect(*args)
Context_disconnect = _oboe_ext.Context_disconnect

def Context_reconnect(*args):
  return _oboe_ext.Context_reconnect(*args)
Context_reconnect = _oboe_ext.Context_reconnect

def Context_shutdown():
  return _oboe_ext.Context_shutdown()
Context_shutdown = _oboe_ext.Context_shutdown

def Context_createEvent():
  return _oboe_ext.Context_createEvent()
Context_createEvent = _oboe_ext.Context_createEvent

def Context_startTrace():
  return _oboe_ext.Context_startTrace()
Context_startTrace = _oboe_ext.Context_startTrace

class Event(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Event, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Event, name)
    def __init__(self, *args, **kwargs): raise AttributeError("No constructor defined")
    __repr__ = _swig_repr
    __swig_destroy__ = _oboe_ext.delete_Event
    __del__ = lambda self : None;
    def addInfo(self, *args): return _oboe_ext.Event_addInfo(self, *args)
    def addEdge(self, *args): return _oboe_ext.Event_addEdge(self, *args)
    def addEdgeStr(self, *args): return _oboe_ext.Event_addEdgeStr(self, *args)
    def getMetadata(self): return _oboe_ext.Event_getMetadata(self)
    def metadataString(self): return _oboe_ext.Event_metadataString(self)
    def send(self): return _oboe_ext.Event_send(self)
    __swig_getmethods__["startTrace"] = lambda x: _oboe_ext.Event_startTrace
    if _newclass:startTrace = staticmethod(_oboe_ext.Event_startTrace)
Event_swigregister = _oboe_ext.Event_swigregister
Event_swigregister(Event)

def Event_startTrace(*args):
  return _oboe_ext.Event_startTrace(*args)
Event_startTrace = _oboe_ext.Event_startTrace

class Reporter(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Reporter, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Reporter, name)
    __repr__ = _swig_repr
    def __init__(self, *args): 
        this = _oboe_ext.new_Reporter(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _oboe_ext.delete_Reporter
    __del__ = lambda self : None;
    def sendReport(self, *args): return _oboe_ext.Reporter_sendReport(self, *args)
Reporter_swigregister = _oboe_ext.Reporter_swigregister
Reporter_swigregister(Reporter)

class UdpReporter(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, UdpReporter, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, UdpReporter, name)
    __repr__ = _swig_repr
    def __init__(self, *args): 
        this = _oboe_ext.new_UdpReporter(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _oboe_ext.delete_UdpReporter
    __del__ = lambda self : None;
    def sendReport(self, *args): return _oboe_ext.UdpReporter_sendReport(self, *args)
UdpReporter_swigregister = _oboe_ext.UdpReporter_swigregister
UdpReporter_swigregister(UdpReporter)

class FileReporter(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FileReporter, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FileReporter, name)
    __repr__ = _swig_repr
    def __init__(self, *args): 
        this = _oboe_ext.new_FileReporter(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _oboe_ext.delete_FileReporter
    __del__ = lambda self : None;
    def sendReport(self, *args): return _oboe_ext.FileReporter_sendReport(self, *args)
FileReporter_swigregister = _oboe_ext.FileReporter_swigregister
FileReporter_swigregister(FileReporter)

class DebugLogger(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, DebugLogger, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, DebugLogger, name)
    def __init__(self, *args, **kwargs): raise AttributeError("No constructor defined - class is abstract")
    __repr__ = _swig_repr
    def log(self, *args): return _oboe_ext.DebugLogger_log(self, *args)
    __swig_destroy__ = _oboe_ext.delete_DebugLogger
    __del__ = lambda self : None;
DebugLogger_swigregister = _oboe_ext.DebugLogger_swigregister
DebugLogger_swigregister(DebugLogger)


def oboe_debug_log_handler(*args):
  return _oboe_ext.oboe_debug_log_handler(*args)
oboe_debug_log_handler = _oboe_ext.oboe_debug_log_handler
class DebugLog(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, DebugLog, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, DebugLog, name)
    __repr__ = _swig_repr
    __swig_getmethods__["getLevelName"] = lambda x: _oboe_ext.DebugLog_getLevelName
    if _newclass:getLevelName = staticmethod(_oboe_ext.DebugLog_getLevelName)
    __swig_getmethods__["getModuleName"] = lambda x: _oboe_ext.DebugLog_getModuleName
    if _newclass:getModuleName = staticmethod(_oboe_ext.DebugLog_getModuleName)
    __swig_getmethods__["getLevel"] = lambda x: _oboe_ext.DebugLog_getLevel
    if _newclass:getLevel = staticmethod(_oboe_ext.DebugLog_getLevel)
    __swig_getmethods__["setLevel"] = lambda x: _oboe_ext.DebugLog_setLevel
    if _newclass:setLevel = staticmethod(_oboe_ext.DebugLog_setLevel)
    __swig_getmethods__["setOutputStream"] = lambda x: _oboe_ext.DebugLog_setOutputStream
    if _newclass:setOutputStream = staticmethod(_oboe_ext.DebugLog_setOutputStream)
    __swig_getmethods__["setOutputFile"] = lambda x: _oboe_ext.DebugLog_setOutputFile
    if _newclass:setOutputFile = staticmethod(_oboe_ext.DebugLog_setOutputFile)
    __swig_getmethods__["addDebugLogger"] = lambda x: _oboe_ext.DebugLog_addDebugLogger
    if _newclass:addDebugLogger = staticmethod(_oboe_ext.DebugLog_addDebugLogger)
    __swig_getmethods__["removeDebugLogger"] = lambda x: _oboe_ext.DebugLog_removeDebugLogger
    if _newclass:removeDebugLogger = staticmethod(_oboe_ext.DebugLog_removeDebugLogger)
    __swig_getmethods__["logMessage"] = lambda x: _oboe_ext.DebugLog_logMessage
    if _newclass:logMessage = staticmethod(_oboe_ext.DebugLog_logMessage)
    def __init__(self): 
        this = _oboe_ext.new_DebugLog()
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _oboe_ext.delete_DebugLog
    __del__ = lambda self : None;
DebugLog_swigregister = _oboe_ext.DebugLog_swigregister
DebugLog_swigregister(DebugLog)

def DebugLog_getLevelName(*args):
  return _oboe_ext.DebugLog_getLevelName(*args)
DebugLog_getLevelName = _oboe_ext.DebugLog_getLevelName

def DebugLog_getModuleName(*args):
  return _oboe_ext.DebugLog_getModuleName(*args)
DebugLog_getModuleName = _oboe_ext.DebugLog_getModuleName

def DebugLog_getLevel(*args):
  return _oboe_ext.DebugLog_getLevel(*args)
DebugLog_getLevel = _oboe_ext.DebugLog_getLevel

def DebugLog_setLevel(*args):
  return _oboe_ext.DebugLog_setLevel(*args)
DebugLog_setLevel = _oboe_ext.DebugLog_setLevel

def DebugLog_setOutputStream(*args):
  return _oboe_ext.DebugLog_setOutputStream(*args)
DebugLog_setOutputStream = _oboe_ext.DebugLog_setOutputStream

def DebugLog_setOutputFile(*args):
  return _oboe_ext.DebugLog_setOutputFile(*args)
DebugLog_setOutputFile = _oboe_ext.DebugLog_setOutputFile

def DebugLog_addDebugLogger(*args):
  return _oboe_ext.DebugLog_addDebugLogger(*args)
DebugLog_addDebugLogger = _oboe_ext.DebugLog_addDebugLogger

def DebugLog_removeDebugLogger(*args):
  return _oboe_ext.DebugLog_removeDebugLogger(*args)
DebugLog_removeDebugLogger = _oboe_ext.DebugLog_removeDebugLogger

def DebugLog_logMessage(*args):
  return _oboe_ext.DebugLog_logMessage(*args)
DebugLog_logMessage = _oboe_ext.DebugLog_logMessage

class Config(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Config, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Config, name)
    __repr__ = _swig_repr
    __swig_getmethods__["checkVersion"] = lambda x: _oboe_ext.Config_checkVersion
    if _newclass:checkVersion = staticmethod(_oboe_ext.Config_checkVersion)
    __swig_getmethods__["getVersion"] = lambda x: _oboe_ext.Config_getVersion
    if _newclass:getVersion = staticmethod(_oboe_ext.Config_getVersion)
    __swig_getmethods__["getRevision"] = lambda x: _oboe_ext.Config_getRevision
    if _newclass:getRevision = staticmethod(_oboe_ext.Config_getRevision)
    def __init__(self): 
        this = _oboe_ext.new_Config()
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _oboe_ext.delete_Config
    __del__ = lambda self : None;
Config_swigregister = _oboe_ext.Config_swigregister
Config_swigregister(Config)

def Config_checkVersion(*args):
  return _oboe_ext.Config_checkVersion(*args)
Config_checkVersion = _oboe_ext.Config_checkVersion

def Config_getVersion():
  return _oboe_ext.Config_getVersion()
Config_getVersion = _oboe_ext.Config_getVersion

def Config_getRevision():
  return _oboe_ext.Config_getRevision()
Config_getRevision = _oboe_ext.Config_getRevision

# This file is compatible with both classic and new-style classes.



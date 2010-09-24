# WSGI middleware for Oboe support
import oboe

# taken from PyVM http://desk.stinkpot.org:8080/downloads/PyVM.py
#
# PyVM is linux-only, but this would be slightly more portable:
#   http://www.pixelbeat.org/scripts/ps_mem.py
#
import os
_proc_status = '/proc/%d/status' % os.getpid()
_scale = {'kB': 1024.0, 'mB': 1024.0*1024.0,
          'KB': 1024.0, 'MB': 1024.0*1024.0}
_total_memory = 0.0
_last_memory = 0.0

def _VmB(VmKey):
    '''private method'''
    global _proc_status, _scale
    # get pseudo file  /proc/<pid>/status
    try:
        t = open(_proc_status)
        v = t.read()
        t.close()
    except:
        return 0.0  # non-Linux?
    # get VmKey line e.g. 'VmRSS:  9999  kB\n ...'
    i = v.index(VmKey)
    v = v[i:].split(None, 3)  # whitespace
    if len(v) < 3:
        return 0.0  # invalid format?
    # convert Vm value to bytes
    return (float(v[1]) * _scale[v[2]])

def MemoryDiff():
    ''' print memory usage stats in bytes.
        returns a tuple each time executed: (current size, delta since last call)
    '''
    global _total_memory, _last_memory

    _last_memory = _total_memory
    from pympler.muppy import muppy
    _total_memory = muppy.get_size(muppy.get_objects())
#    _total_memory = _VmB('VmSize:')

    mem_diff = _total_memory - _last_memory
    return _total_memory, mem_diff

class OboeMiddleware:
    def __init__(self, app, oboe_config):
        """
        Takes the app that we're wrapping, as well as a dictionary with oboe
        configuration parameters:

          - tracing_mode: 'always', 'through', 'never'
          - reporter_host: Hostname
        """

        self.wrapped_app = app
        self.oboe_config = oboe_config

    def __call__(self, environ, start_response):
        xtr_hdr = environ.get("HTTP_X-Trace", environ.get("HTTP_X_TRACE"))
        evt, endEvt = None, None
        mem_tracker = None
        
        tracing_mode = self.oboe_config.get('oboe.tracing_mode')

        if xtr_hdr and tracing_mode in ['always', 'through']:
            oboe.Context.fromString(xtr_hdr)

        if not oboe.Context.isValid() and tracing_mode == "always":
            evt = oboe.Context.startTrace()
        elif oboe.Context.isValid() and tracing_mode != 'never':
            evt = oboe.Context.createEvent()

        if oboe.Context.isValid() and tracing_mode != 'never':
            evt.addInfo("Agent", "wsgi")
            evt.addInfo("Label", "entry")
            reporter = oboe.UdpReporter(self.oboe_config.get('oboe.reporter_host'))
            reporter.sendReport(evt)

            endEvt = oboe.Context.createEvent()

            add_header = True
            MemoryDiff()
        else:
            add_header = False

        
        def wrapped_start_response(status, headers):
            if add_header: headers.append(("X-Trace", endEvt.metadataString()))
            start_response(status, headers)

        result = self.wrapped_app(environ, wrapped_start_response)

        # TODO: Should we handle starting a trace here?
        if oboe.Context.isValid() and tracing_mode != 'never' and endEvt:
            print "taking t2"
            mem_diff = MemoryDiff() 
            print "done"
            evt = endEvt

            evt.addEdge(oboe.Context.get())
            evt.addInfo("Agent", "wsgi")
            evt.addInfo("Label", "exit")
            print "adding delta"
#            if mem_diff:
#                import json
#                evt.addInfo("Memory-Diff", json.dumps(mem_diff))
            print "done"

            # gets controller, agent
            for k, v in  environ.get('wsgiorg.routing_args')[1].items():
                evt.addInfo(str(k).capitalize(), str(v))

            reporter = oboe.UdpReporter(self.oboe_config.get('oboe.reporter_host'))
            reporter.sendReport(evt)
            
            endEvt = None

        return result

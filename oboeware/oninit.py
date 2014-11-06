""" Tracelytics initialization function(s).

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
import oboeware
import oboe
import sys
import copy

def report_layer_init(layer="wsgi"):
    """ Send a fake trace showing the initialization and version of this layer's
        instrumentation. """

    ver_keys = {}
    ver_keys["__Init"] = 1
    ver_keys["Force"] = True
    ver_keys["Python.Version"] = sys.version
    ver_keys["Python.Oboe.Version"] = oboe.__version__

    if 'tornado' in sys.modules:
        ver_keys["Python.Tornado.Version"] = sys.modules['tornado'].version

    if 'django' in sys.modules:
        try:
            import django
            ver_keys["Python.Django.Version"] = django.get_version()
        except ImportError:
            pass

    oboe.start_trace(layer, store_backtrace=False, keys=ver_keys)
    oboe.end_trace(layer)


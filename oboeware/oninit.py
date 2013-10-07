""" Tracelytics initialization function(s).

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
import oboe
import oboeware
import sys
import copy

def report_layer_init(layer="wsgi"):
    """ Send a fake trace showing the initialization and version of this layer's
        instrumentation. """

    django_version = 'none'
    try:
        import django
        django_version = django.get_version()
    except ImportError:
        pass

    tornado_version = 'none'
    if 'tornado' in sys.modules:
        tornado_version = sys.modules['tornado'].version

    ver_keys = {"__Init": 1,
                "Force": True,
                "Python.Version": sys.version,
                "Python.Oboe.Version": oboe.__version__,
                "Python.Django.Version": django_version,
                "Python.Tornado.Version": tornado_version}

    oboe.start_trace(layer, store_backtrace=False, keys=ver_keys)
    oboe.end_trace(layer)


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
    # force trace, save old config
    tmp_config = copy.deepcopy(oboe.config)
    oboe.config['tracing_mode'] = 'always'
    oboe.config['sample_rate'] = 1.0

    django_version = 'none'
    try:
        import django
        django_version = django.get_version()
    except ImportError:
        pass

    ver_keys = {"__Init": 1,
                "PyVersion": sys.version,
                "OboePythonVersion": oboe.__version__,
                "DjangoVersion": django_version}

    oboe.start_trace(layer, store_backtrace=False, keys=ver_keys)
    oboe.end_trace(layer)

    # restore old config
    oboe.config = tmp_config

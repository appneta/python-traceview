""" Tracelytics initialization function(s).

Copyright (C) 2011 by Tracelytics, Inc.
All rights reserved.
"""
import oboe
import oboeware
import sys

def report_layer_init(layer="wsgi"):
    """ Send a fake trace showing the initialization and version of this layer's
        instrumentation. """
    # Use logs instead of start/end_trace to avoid sampling
    oboe.log("entry", layer, keys={"__Init": 1, "PyVersion": sys.version})
    oboe.log("exit", layer)
    oboe.Context.clear_default()

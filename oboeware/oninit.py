# Copyright (C) 2011 by Tracelytics, Inc.
# All rights reserved.

import oboe
import oboeware

def report_layer_init(layer="wsgi"):
    """ Send a fake trace showing the initialization and version of this layer's
        instrumentation. """
    evt = oboe.Context.startTrace()
    evt.addInfo("Layer", layer)
    evt.addInfo("Label", "entry")
    evt.addInfo("__Init", 1)
    evt.addInfo("Version", oboeware.__version__)
    oboe.reporter().sendReport(evt)

    evt = oboe.Context.createEvent()
    evt.addInfo("Layer", layer)
    evt.addInfo("Label", "exit")
    oboe.reporter().sendReport(evt)

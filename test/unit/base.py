""" Base utilities for testing oboeware """

import sys
import os

def force_local_oboeware():
    basepath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
    oboeware_path = os.path.join(basepath, 'oboeware')
    # ensure that instrumentation from the oboeware folder gets included before anything in the venv
    sys.path.insert(0, oboeware_path)

def enable_mock_oboe():
    basepath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
    oboe_path = os.path.join(basepath, 'oboe')
    mockoboe_path = os.path.join(basepath, 'test', 'unit')
    import shutil
    for f in ['__init__.py', 'backport.py']:
        shutil.copy(os.path.join(oboe_path, f), os.path.join(mockoboe_path, 'oboe', f))
    sys.path.insert(0, mockoboe_path)

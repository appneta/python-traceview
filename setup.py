#!/usr/bin/env python

# Copyright (C) 2011 by Tracelytics, Inc.
# All rights reserved.


from setuptools import setup
import oboeware

setup(name = 'oboe',
      version = oboeware.__version__,
      author = 'Tracelytics',
      author_email = 'contact@tracelytics.com',
      url = 'http://www.tracelytics.com',
      download_url = 'http://pypi.tracelytics.com/oboeware',
      description  = 'Tracelytics Oboe libraries, instrumentation and web middleware components for WSGI, Django, and Tornado.',
      packages = ['oboe', 'oboeware'],
      license = 'Tracelytics Alpha Agreement',
      )

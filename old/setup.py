#!/usr/bin/env python

# Copyright (C) 2016 by SolarWinds, LLC.
# All rights reserved.


from setuptools import setup, Extension
version = '0.4.0'

setup(name = 'oboeware',
      version = version,
      author = 'Tracelytics',
      author_email = 'contact@tracelytics.com',
      url = 'http://www.tracelytics.com',
      description  = 'This package has been deprecated: only "oboe" is required.',
      packages = ['oboeware'],
      install_requires=['oboe>=0.4.0'],
      license = 'Tracelytics Alpha Agreement',
      )

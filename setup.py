#!/usr/bin/env python

# Copyright (C) 2011 by Tracelytics, Inc.
# All rights reserved.


from setuptools import setup

# TODO: Require oboe as a dependency. This may requrie switching to setuptools
setup(name = 'oboeware',
      version = '0.1.0',
      author = 'Tracelytics',
      author_email = 'contact@tracelytics.com',
      url = 'http://www.tracelytics.com',
      download_url = 'http://pypi.tracelytics.com/oboeware',
      description  = 'Oboe middleware for WSGI',
      packages = ['oboeware'],
      license = 'Tracelytics Alpha Agreement'
      package_dir = {'oboeware' : 'src'}
      )

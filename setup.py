#!/usr/bin/env python

# Copyright (C) 2011 by Tracelytics, Inc.
# All rights reserved.


from setuptools import setup

setup(name = 'oboeware',
      version = '0.2.2',
      author = 'Tracelytics',
      author_email = 'contact@tracelytics.com',
      url = 'http://www.tracelytics.com',
      download_url = 'http://pypi.tracelytics.com/oboeware',
      description  = 'Oboe middleware for WSGI',
      packages = ['oboeware'],
      license = 'Tracelytics Alpha Agreement',
      package_dir = {'oboeware' : 'src'},
      install_requires = ['oboe>=0.1.8.4']
      )

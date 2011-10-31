#!/usr/bin/env python

# Copyright (C) 2011 by Tracelytics, Inc.
# All rights reserved.


from setuptools import setup, Extension
version = '0.4.0'

oboe_module = Extension('oboe._oboe_ext', 
                        sources=['oboe/oboe_wrap.cxx'], 
                        depends=['oboe/oboe.hpp'], 
                        libraries=['oboe'])

setup(name = 'oboe',
      version = version,
      author = 'Tracelytics',
      author_email = 'contact@tracelytics.com',
      url = 'http://www.tracelytics.com',
      download_url = 'http://pypi.tracelytics.com/oboeware',
      description  = 'Tracelytics Oboe libraries, instrumentation and web middleware components for WSGI, Django, and Tornado.',
      ext_modules = [oboe_module],
      packages = ['oboe', 'oboeware'],
      license = 'Tracelytics Alpha Agreement',
      install_requires = ['decorator'],
      )

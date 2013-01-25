#!/usr/bin/env python
"""
 Copyright (C) 2011 by Tracelytics, Inc.
 All rights reserved.
"""

import distutils.ccompiler
from setuptools import setup, Extension
version = '1.3.8'

# conditionally build extensions if liboboe and liboboe-dev are available on this platform
# otherwise, will function in no-op mode: no tracing, but all API endpoints available
compiler = distutils.ccompiler.new_compiler()
if compiler.has_function('oboe_metadata_init', libraries=('oboe',)):
    oboe_module = Extension('oboe._oboe_ext',
                            sources=['oboe/oboe_wrap.cxx'],
                            depends=['oboe/oboe.hpp'],
                            libraries=['oboe'])
    ext_modules = [oboe_module]
else:
    ext_modules = []

setup(name = 'oboe',
      version = version,
      author = 'Tracelytics',
      author_email = 'contact@tracelytics.com',
      url = 'http://www.tracelytics.com',
      download_url = 'http://pypi.tracelytics.com/oboeware',
      description  = 'Tracelytics Oboe libraries, instrumentation and web middleware components '
      'for WSGI, Django, and Tornado.',
      long_description = open('README.txt').read(),
      keywords='tracelytics oboe liboboe instrumentation performance wsgi middleware django',
      ext_modules = ext_modules,
      packages = ['oboe', 'oboeware'],
      license = 'LICENSE.txt',
      install_requires = ['decorator'],
      )

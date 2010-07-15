#!/usr/bin/env python

from distutils.core import setup

# TODO: Require oboe as a dependency. This may requrie switching to setuptools
setup(name = 'oboeware',
      version = '0.1.0',
      author = 'Spiridon Eliopoulos',
      description  = 'Oboe middleware for WSGI',
      packages = ['oboeware'],
      package_dir = {'oboeware' : 'src'}
      )

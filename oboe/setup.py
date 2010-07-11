#!/usr/bin/env python

from distutils.core import setup, Extension

oboe_module = Extension('_oboe', sources=['oboe_wrap.cxx'], libraries=['oboe'])

setup(name = 'oboe',
      version = '0.1.0',
      author = 'Spiridon Eliopoulos',
      description = 'Oboe API for Python',
      ext_modules = [oboe_module],
      py_modules = ['oboe'],
      )

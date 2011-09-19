#!/usr/bin/env python

from setuptools import setup, Extension

oboe_module = Extension('_oboe_ext', sources=['oboe_wrap.cxx'], depends=['oboe.hpp'], libraries=['oboe'])

setup(name = 'oboe',
      version = '0.1.9.1',
      author = 'Tracelytics',
      author_email = 'contact@tracelytics.com',
      url = 'http://www.tracelytics.com',
      download_url = 'http://pypi.tracelytics.com/oboe',
      description = 'Oboe API for Python',
      ext_modules = [oboe_module],
      py_modules = ['oboe_ext', 'oboe'],
      install_requires = ['decorator'],
      )

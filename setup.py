#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from setuptools import setup
import re
import os
import sys

# load version form _version.py
VERSIONFILE = "sif_reader/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

# module

setup(name='sif_reader',
      version=verstr,
      author="Keisuke Fujii",
      author_email="fujii@me.kyoto-u.ac.jp",
      description=("Python package to read Andor sif file."),
      license="BSD 3-clause",
      keywords="imaging, Andor",
      url="http://github.com/fujii-team/sif_reader",
      packages=["sif_reader"],
      package_dir={'sif_reader': 'sif_reader'},
      py_modules=['sif_reader.__init__'],
      test_suite='testings',
      install_requires="""
        numpy>=1.10
      """,
      classifiers=['License :: OSI Approved :: BSD License',
                   'Natural Language :: English',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 3.6',
                   'Topic :: Scientific/Engineering :: Physics'],
      entry_points={
          'console_scripts': [
              'sif_reader=sif_reader.__main__:_main'
              ]
          }
      )

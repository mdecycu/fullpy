#! /usr/bin/env python
# -*- coding: utf-8 -*-
# FullPy
# Copyright (C) 2022-2023 Jean-Baptiste LAMY

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os, os.path, sys, glob

HERE = os.path.relpath(os.path.dirname(os.path.abspath(__file__)))

if len(sys.argv) <= 1: sys.argv.append("install")

import setuptools

version = open(os.path.join(HERE, "__init__.py")).read().split('VERSION = "', 1)[1].split('"', 1)[0]

def do_setup(extensions):
  return setuptools.setup(
  name         = "fullpy",
  version      = version,
  license      = "LGPLv3+",
  description  = "A module for developping client-server web application entirely in Python, with semantic data persistance using OWL ontologies and remote function calls (RPC) via Ajax or WebSocket.",
  long_description = open(os.path.join(HERE, "README.rst")).read(),
    
  author       = "Lamy Jean-Baptiste (Jiba)",
  author_email = "jibalamy@free.fr",
  url          = "https://bitbucket.org/jibalamy/fullpy",
  classifiers  = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Intended Audience :: Information Technology",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
  
  package_dir  = {"fullpy" : HERE},
  packages     = ["fullpy", "fullpy.client", "fullpy.server"],
  package_data = {"fullpy" : ["server/fullpy.owl",
                              "static/fullpy.css",
                              ]},
  
  install_requires = [
    'brython',
    'owlready2',
    'gunicorn',
    'gevent',
    'flask',
  ],
  )

dist = do_setup([])


if len(sys.argv) >= 2 and sys.argv[1] == "develop":
    # `python setup.py develop` (and `pip install -e .`) assumes a directory structure
    # where the package to be installed lives in a subirectory.
    # However, to maintain backward compatibility, this package is structured
    # differently. To allow `python setup.py develop` anyway, we do some manual
    # tweaks.

    # Note: relative import not possible here due to PEP 338
    # Thus, we use an absolute import assuming that the name is unique
    # noinspection PyUnresolvedReferences
    from setup_develop_mode import install_develop_mode
    install_develop_mode(dist)

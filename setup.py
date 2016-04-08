#!/usr/bin/env python3

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path
import re

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

version = ''
with open('mpv/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)


setup(
    name='mpv',
    version=version,
    py_modules=['mpv'],
    description=('A python interface to the mpv media player'),
    url='https://github.com/jaseg/python-mpv',
    author='jaseg',
    author_email='github@jaseg.net',
    maintainer='Cory Parsons',
    maintainer_email='parsons.cory@gmail.com',
    license='AGPLv2',
    package_data={'': ['LICENSE']},
)

#!/usr/bin/env python3

# Always prefer setuptools over distutils
from setuptools import setup
# To use a consistent encoding
from codecs import open
from os import path
import re

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open('mpv/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')


setup(
    name='mpv',
    version=version,
    description=('A python interface to the mpv media player'),
    url='https://github.com/coryo/python-mpv',
    author='jaseg',
    author_email='github@jaseg.net',
    maintainer='Cory Parsons',
    maintainer_email='parsons.cory@gmail.com',
    license='AGPLv2',
    packages=['mpv'],
    data_files=[('', ['LICENSE'])],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)

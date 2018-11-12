# Xylem: Convert Python Abstract Syntax Trees to readable source code
# Copyright (C) 2018 Ariel Antonitis. Licensed under the MIT license.
#
# setup.py
from setuptools import setup

from xylem import __version__, url

with open('README.rst', 'r') as f:
    long_description = f.read()

setup(name='xylem',
      version=__version__,
      description='Convert Python Abstract Syntax Trees to readable source code',
      long_description=long_description,
      author='Ariel Antonitis',
      author_email='arant@mit.edu',
      url=url,
      py_modules=['xylem'],
      package_data={'*': ['README.rst', 'test.py']},
      license='MIT',
      classifiers=['License :: OSI Approved :: MIT License',
                   'Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'Topic :: Software Development :: Code Generators',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6',
                   'Programming Language :: Python :: 3.7'],
      python_requires='>=3.4')

#!/usr/bin/env python
"""
Pyomo Solver Performance Benchmarking Library
"""
import sys

from setuptools import setup, find_packages


def warn(s):
    sys.stderr.write('*** WARNING *** {}\n'.format(s))


kwargs = dict(
    name='pysperf',
    packages=find_packages(),
    install_requires=[],
    extras_require={},
    package_data={
        # If any package contains *.template or *.json files, include them:
        '': ['*.template', '*.json']
    },
    scripts=[],
    author='Qi Chen',
    author_email='qichen@andrew.cmu.edu',
    maintainer='Qi Chen',
    url="https://github.com/qtothec/pysperf",
    license='BSD 2-clause',
    description="Pyomo Solver Performance Benchmarking Library",
    long_description=__doc__,
    data_files=[],
    keywords=["pyomo", "generalized disjunctive programming"],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    entry_points="""\
        [console_scripts]
        pysperf=pysperf.__main__:main
    """
)

try:
    setup(setup_requires=['setuptools_scm'], use_scm_version=True, **kwargs)
except (ImportError, LookupError):
    default_version = '1.0.0'
    warn('Cannot use .git version: package setuptools_scm not installed '
         'or .git directory not present.')
    print('Defaulting to version: {}'.format(default_version))
    setup(**kwargs)

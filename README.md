# Pysperf
Pyomo Solver Performance Analysis Library

## Installation

Pysperf may be install from PyPI using:

``pip install pysperf``

## Example commands:

After installation, the following commands are available

### Listing library elements
- ``pysperf list models``
- ``pysperf list solvers``
- ``pysperf list runs``
### Performing runs
- ``pysperf run --new``
- ``pysperf run --new --model 8PP --solvers BARON-BM``
- ``pysperf run --new --model-types GDP cvxGDP --solvers GDPopt-LBB``
- ``pysperf run --redo -r2 --redo-existing --redo-failed`` Redo all of run 2
### Analyzing complete runs
- ``pysperf analyze`` Analyze last run (options cache still beta code)
- ``pysperf analyze -r3`` Analyze run 3
### Exporting data
- ``pysperf export --make-solu-file --make-trace-file --to-excel -r 5`` export run 5

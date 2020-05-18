# Pysperf
Pyomo Solver Performance Analysis Library


## Example commands:

To use the commands below (Unix), you must put a python script that imports and executes `parse_command_line_arguments_and_run()` from `pysperf.pysperf_main` in your system PATH. Otherwise, you will need to type `python pysperf_main.py list models` and so on.

### Listing library elements
- `pysperf list models`
- `pysperf list solvers`
- `pysperf list runs`
### Performing runs
- `pysperf run --new`
- `pysperf run --redo -r2 --redo-existing --redo-failed`
### Analyzing complete runs
- `pysperf analyze` Analyze last run (options cache still beta code)
- `pysperf analyze -r3` Analyze run 3
### Exporting data
- `pysperf export --make-solu-file --make-trace-file --to-excel -r 5` export run 5

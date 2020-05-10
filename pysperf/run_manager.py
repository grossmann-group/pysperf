import sys
from pathlib import Path

from pysperf.model_library import models
from pysperf.solver_library import solvers


def execute_matrix_run():
    # create matrix of jobs to run
    jobs = {
        (model_name, solver_name)
        for model_name, model in models.items()
        for solver_name, solver in solvers.items()
        if model.model_type in solver.compatible_model_types
    }
    print(jobs)
    # create directories and files
    # Make output directory, if it does not exist
    runsdir = Path("output/runs/")
    runsdir.mkdir(exist_ok=True)
    # Make a new run directory
    rundirs = set(rundir.name for rundir in runsdir.glob("run*/"))
    next_run_num = 1
    next_run_dir = f"run{next_run_num}"
    while next_run_dir in rundirs:
        next_run_num += 1
        next_run_dir = f"run{next_run_num}"
    this_run_dir = runsdir.joinpath(next_run_dir)
    this_run_dir.mkdir(exist_ok=False)
    # Make solver/model directories
    for model_name, solver_name in jobs:
        single_run_dir = this_run_dir.joinpath(solver_name, model_name)
        single_run_dir.mkdir(parents=True, exist_ok=False)
        # submit job
        # build execution script
        runner_file = Path("pysperf_runner.py")
        execute_script = f"""
#!/bin/bash

cd {single_run_dir.resolve()}
{sys.executable} {runner_file.resolve()} > >(tee -a stdout.log) 2> >(tee -a stderr.log >&2)
        """.strip() + "\n"
        single_run_dir.joinpath("single_run.sh").write_text(execute_script)
        # Submit job for execution
    pass

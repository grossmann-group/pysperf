"""Runs test jobs in serial."""
import subprocess

import yaml

from pysperf import options
from run_manager import get_current_run_dir, get_time_limit_with_buffer


def execute_run():
    # Read in config
    # Start executing the *.sh files
    this_run_dir = get_current_run_dir()
    with this_run_dir.joinpath("run.queue.pfcache").open('r') as runcache:
        jobs = yaml.safe_load(runcache)
    for jobnum, (model_name, solver_name) in enumerate(jobs, start=1):
        current_run_num = options["current run number"]
        print(f"Running run {current_run_num}-{jobnum}/{len(jobs)}: Solver {solver_name} with model {model_name}.")
        runner_script = this_run_dir.joinpath(solver_name, model_name, "single_run.sh")
        try:
            subprocess.run(
                str(runner_script.resolve()),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=get_time_limit_with_buffer()
            )
        except subprocess.TimeoutExpired:
            pass

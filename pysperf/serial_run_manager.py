"""Runs test jobs in serial."""
import subprocess

import yaml

from run_manager import get_current_run_dir


def execute_run():
    # Read in config
    # Start executing the *.sh files
    this_run_dir = get_current_run_dir()
    with this_run_dir.joinpath("run.queue.pfcache").open('r') as runcache:
        jobs = yaml.safe_load(runcache)
    for model_name, solver_name in jobs:
        print(f"Benchmarking {solver_name} with model {model_name}.")
        runner_script = this_run_dir.joinpath(solver_name, model_name, "single_run.sh")
        subprocess.run(str(runner_script.resolve()), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

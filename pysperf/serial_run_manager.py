"""Runs test jobs in serial."""
import subprocess

import yaml

from pysperf import options
from pysperf.model_library import models
from .run_manager import get_run_dir, get_time_limit_with_buffer, this_run_config


def execute_run():
    # Read in config
    # Start executing the *.sh files
    this_run_dir = get_run_dir()
    with this_run_dir.joinpath("run.config.pfdata").open('r') as runcache:
        _run_options = yaml.safe_load(runcache)
        this_run_config.update(_run_options)
        jobs = this_run_config.jobs
    for jobnum, (model_name, solver_name) in enumerate(jobs, start=1):
        current_run_num = options["current run number"]
        print(f"Executing run {current_run_num}-{jobnum}/{len(jobs)}: Solver {solver_name} with model {model_name}.")
        runner_script = this_run_dir.joinpath(solver_name, model_name, "run_job.sh")
        try:
            subprocess.run(
                str(runner_script.resolve()),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=get_time_limit_with_buffer(models[model_name].build_time)
            )
        except subprocess.TimeoutExpired:
            pass

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
        print(f"Submitting run {current_run_num}-{jobnum}/{len(jobs)}: Solver {solver_name} with model {model_name}.")
        runner_script = this_run_dir.joinpath(solver_name, model_name, "run_job.sh")
        time_limit = options.time_limit
        qsub_time_limit = _qsub_time_limit_with_buffer(models[model_name].build_time)
        processes = options.processes
        memory = options.memory
        subprocess.run([
            "qsub", "-l",
            f"walltime={qsub_time_limit},nodes=1:ppn={processes},mem={memory}GB",
            # TODO qsub is very finicky about what -N values it accepts. We will need to experiment with this.
            # Not high priority, since it is only cosmetic.
            # f'-N "pysperf-r{current_run_num}-{jobnum}:{len(jobs)}-t{time_limit}s"',
            f"{runner_script.resolve()}"
        ])


def _qsub_time_limit_with_buffer(model_build_time):
    time_limit = get_time_limit_with_buffer(model_build_time)
    hours, time_limit = divmod(time_limit, 3600)
    minutes, time_limit = divmod(time_limit, 60)
    seconds = round(time_limit)
    return "{:02d}:{:02d}:{:02d}".format(int(hours), int(minutes), int(seconds))

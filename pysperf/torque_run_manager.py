import subprocess

import yaml

from pysperf import options
from pysperf.model_library import models
from .run_manager import _load_run_config, get_run_dir, get_time_limit_with_buffer, this_run_config


def execute_run():
    # Read in config
    # Start executing the *.sh files
    this_run_dir = get_run_dir()
    _load_run_config(this_run_dir)
    jobs = this_run_config.jobs_to_run
    for jobnum, (model_name, solver_name) in enumerate(jobs, start=1):
        current_run_num = options["current run number"]
        print(f"Submitting run {current_run_num}-{jobnum}/{len(jobs)}: Solver {solver_name} with model {model_name}.")
        runner_script = this_run_dir.joinpath(solver_name, model_name, "run_job.sh")
        time_limit = options.time_limit
        qsub_time_limit = _qsub_time_limit_with_buffer(models[model_name].build_time)
        processes = options.processes
        memory = options.memory
        qsub_N_arg = f'r{int(current_run_num)}-{jobnum}:{len(jobs)}-t{int(time_limit)}s'
        qsub_N_arg = qsub_N_arg[:15]  # TODO qsub -N flag only accepts up to 15 characters. Truncate for now.
        subprocess.run([
            "qsub", "-l",
            f"walltime={qsub_time_limit},nodes=1:ppn={processes},mem={memory}GB",
            "-N", qsub_N_arg,
            f"{runner_script.resolve()}"
        ])


def _qsub_time_limit_with_buffer(model_build_time):
    time_limit = get_time_limit_with_buffer(model_build_time)
    hours, time_limit = divmod(time_limit, 3600)
    minutes, time_limit = divmod(time_limit, 60)
    seconds = round(time_limit)
    return "{:02d}:{:02d}:{:02d}".format(int(hours), int(minutes), int(seconds))

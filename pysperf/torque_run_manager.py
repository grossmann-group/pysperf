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
        print(f"Submitting run {current_run_num}-{jobnum}/{len(jobs)}: Solver {solver_name} with model {model_name}.")
        runner_script = this_run_dir.joinpath(solver_name, model_name, "single_run.sh")
        time_limit = options["time limit"]
        qsub_time_limit = _qsub_time_limit_with_buffer()
        processes = options.processes
        memory = options.memory
        subprocess.run([
            "qsub", "-l",
            f"walltime={qsub_time_limit},nodes=1:ppn={processes},mem={memory}GB",
            f'-N "pysperf-r{current_run_num}-{jobnum}:{len(jobs)}-t{time_limit}s"',
            f"{runner_script.resolve()}"
        ])


def _qsub_time_limit_with_buffer():
    time_limit = get_time_limit_with_buffer()
    hours, time_limit = divmod(time_limit, 3600)
    minutes, time_limit = divmod(time_limit, 60)
    seconds = round(time_limit)
    return "{:02d}:{:02d}:{:02d}".format(int(hours), int(minutes), int(seconds))

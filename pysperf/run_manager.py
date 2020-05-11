import stat
import sys
import textwrap
from collections import defaultdict
from math import ceil
from pathlib import Path
from typing import Optional

import yaml

from config import options
from pysperf.model_library import models
from pysperf.solver_library import solvers


# Make output directory, if it does not exist
runsdir = Path("output/runs/")
runsdir.mkdir(exist_ok=True)


def setup_matrix_run():
    # create matrix of jobs to run
    jobs = [
        (model_name, solver_name)
        for model_name, model in models.items()
        for solver_name, solver in solvers.items()
        if model.model_type in solver.compatible_model_types
    ]
    print(jobs)
    # create directories and files
    this_run_dir = make_new_run_dir()
    # Make solver/model directories
    for model_name, solver_name in jobs:
        single_run_dir = this_run_dir.joinpath(solver_name, model_name)
        single_run_dir.mkdir(parents=True, exist_ok=False)
        # build execution script
        runner_file = Path("pysperf_runner.py")
        run_command = (f'{sys.executable} {runner_file.resolve()} '
                       f'"{solver_name}" "{model_name}" "{options["time limit"]}s" '
                       f'> >(tee -a stdout.log) 2> >(tee -a stderr.log >&2)')
        execute_script = f"""\
        #!/bin/bash
        
        cd {single_run_dir.resolve()}
        {run_command}
        """
        execute_script = textwrap.dedent(execute_script)
        single_run_script = single_run_dir.joinpath("single_run.sh")
        single_run_script.write_text(execute_script)
        single_run_script.chmod(single_run_script.stat().st_mode | stat.S_IXUSR)  # chmod u+x
        # create run config
        single_run_config_path = single_run_dir.joinpath("pysperf_runner.config")
        single_run_config = {
            "model name": model_name,
            "solver name": solver_name,
            "time limit": options["time limit"],
        }
        with single_run_config_path.open('w') as single_run_config_file:
            yaml.safe_dump(single_run_config, single_run_config_file)

    # Submit jobs for execution
    with runsdir.joinpath("runs.info.pfcache").open('w') as runsinfofile:
        yaml.safe_dump(dict(**options), runsinfofile)
    with this_run_dir.joinpath("run.queue.pfcache").open('w') as runcache:
        yaml.safe_dump(jobs, runcache)


def make_new_run_dir() -> Path:
    # Make a new run directory
    rundirs = set(rundir.name for rundir in runsdir.glob("run*/"))
    next_run_num = 1
    next_run_dir = f"run{next_run_num}"
    while next_run_dir in rundirs:
        next_run_num += 1
        next_run_dir = f"run{next_run_num}"
    this_run_dir = runsdir.joinpath(next_run_dir)
    this_run_dir.mkdir(exist_ok=False)
    options["current run number"] = next_run_num
    return this_run_dir


def get_current_run_dir() -> Optional[Path]:
    current_run_num = options.get('current run number', None)
    if current_run_num is not None:
        return runsdir.joinpath(f"run{current_run_num}")
    return None


def get_time_limit_with_buffer() -> int:
    time_limit = options["time limit"]
    buffer_percent = options["single run percent buffer"]
    min_buffer = options["single run minimum buffer"]
    time_limit += max(min_buffer, time_limit * buffer_percent / 100)
    return int(ceil(time_limit))


def collect_run_info():
    with runsdir.joinpath("runs.info.pfcache").open('r') as runsinfofile:
        runsinfo = yaml.safe_load(runsinfofile)
        options.update(runsinfo)
    this_run_dir = get_current_run_dir()
    with this_run_dir.joinpath("run.queue.pfcache").open('r') as runcache:
        jobs = yaml.safe_load(runcache)
    started = set()
    model_built = set()
    solve_call_completed = set()
    finished = set()
    for job in jobs:
        job = tuple(job)
        model_name, solver_name = job
        single_run_dir = this_run_dir.joinpath(solver_name, model_name)
        if single_run_dir.joinpath(".single_run_started.log").exists():
            started.add(job)
        if single_run_dir.joinpath(".single_run_model_built.log").exists():
            model_built.add(job)
        if single_run_dir.joinpath(".single_run_solve_called.log").exists():
            solve_call_completed.add(job)
        if single_run_dir.joinpath("pysperf_result.log").exists():
            finished.add(job)
    # Total jobs executed
    print(f"{len(started)} of {len(jobs)} jobs executed.")
    # Model build failures
    jobs_with_failed_model_builds = started - model_built
    models_with_failed_builds = {
        model_name: solver_name for model_name, solver_name in jobs_with_failed_model_builds}
    print(f"{len(models_with_failed_builds)} models had failed builds:")
    for model_name, solver_name in models_with_failed_builds.items():
        print(f" - {model_name} (see {solver_name})")
    # Solver execute failures
    solver_fails = defaultdict(list)
    for model_name, solver_name in started - solve_call_completed:
        solver_fails[solver_name].append(model_name)
    print(f"{len(solver_fails)} solvers had failed executions:")
    for solver_name, failed_list in solver_fails.items():
        print(f" - {solver_name} ({len(failed_list)} failed): {sorted(failed_list)}")
    with this_run_dir.joinpath("solver.failures.log").open('w') as failurelog:
        yaml.safe_dump({k: sorted(v) for k, v in solver_fails.items()}, failurelog, default_flow_style=False)
    # Timeouts and other errors
    print(f"{len(started - finished)} jobs timed out:")
    for model_name, solver_name in started - finished:
        print(f" - {solver_name} {model_name}")

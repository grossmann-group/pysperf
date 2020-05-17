import stat
import sys
import textwrap
from collections import defaultdict
from math import ceil
from pathlib import Path
from typing import Optional

import yaml
from pysperf.model_library import models
from pysperf.solver_library import solvers
from pyutilib.misc import Container

from .config import (
    cache_internal_options_to_file, job_model_built_filename, job_solve_done_filename, job_start_filename,
    job_stop_filename, options, run_config_filename, runner_filepath, runsdir, )

this_run_config = Container()


def _write_run_config(this_run_dir: Path):
    config_to_store = Container(**this_run_config)
    if 'jobs_failed' in config_to_store:
        config_to_store.jobs_failed = [(model, solver) for model, solver in config_to_store.jobs_failed]
    if 'jobs_run' in config_to_store:
        config_to_store.jobs_run = [(model, solver) for model, solver in config_to_store.jobs_run]
    with this_run_dir.joinpath(run_config_filename).open('w') as runinfofile:
        yaml.safe_dump(dict(**config_to_store), runinfofile)


def _read_run_config(this_run_dir: Optional[Path] = None):
    if not this_run_dir:
        this_run_dir = get_run_dir()
    with this_run_dir.joinpath(run_config_filename).open('r') as runinfofile:
        _run_options = yaml.safe_load(runinfofile)
    this_run_config.update(_run_options)
    # Convert things from list back to tuple
    this_run_config.jobs = [(model, solver) for model, solver in this_run_config.jobs]
    if 'jobs_failed' in this_run_config:
        this_run_config.jobs_failed = set((model, solver) for model, solver in this_run_config.jobs_failed)
    if 'jobs_run' in this_run_config:
        this_run_config.jobs_run = set((model, solver) for model, solver in this_run_config.jobs_run)


def setup_new_matrix_run():
    # create matrix of jobs to run
    jobs = [
        (model_name, solver_name)
        for model_name, model in models.items()
        for solver_name, solver in solvers.items()
        if model.model_type in solver.compatible_model_types
    ]
    # Set up run configuration file
    this_run_config.clear()  # clear existing configurations
    this_run_config.jobs = jobs
    this_run_config.time_limit = options.time_limit
    # TODO check that other options don't need to be cached here
    # create directories and files
    this_run_dir = _make_new_run_dir()
    # Make solver/model directories
    for model_name, solver_name in jobs:
        single_job_dir = this_run_dir.joinpath(solver_name, model_name)
        single_job_dir.mkdir(parents=True, exist_ok=False)
        # build execution script
        # Note: this passes unused arguments to the pysperf_runner script, but these show up when
        # other users on the machine look at the running scripts, so it is primarily a service to them.
        run_command = (f'{sys.executable} {runner_filepath} '
                       f'"{solver_name}" "{model_name}" "{options.time_limit}s" '
                       f'> >(tee -a stdout.log) 2> >(tee -a stderr.log >&2)')
        execute_script = f"""\
        #!/bin/bash
        
        cd {single_job_dir.resolve()}
        {run_command}
        """
        execute_script = textwrap.dedent(execute_script)
        single_job_script = single_job_dir.joinpath("run_job.sh")
        single_job_script.write_text(execute_script)
        single_job_script.chmod(single_job_script.stat().st_mode | stat.S_IXUSR)  # chmod u+x
        # create job config
        single_job_config_path = single_job_dir.joinpath("pysperf_job_runner.config")
        single_job_config = {
            "model name": model_name,
            "solver name": solver_name,
            "time_limit": options.time_limit,
        }
        with single_job_config_path.open('w') as single_job_config_file:
            yaml.safe_dump(single_job_config, single_job_config_file)

    # Submit jobs for execution
    cache_internal_options_to_file()
    _write_run_config(this_run_dir)


def _make_new_run_dir() -> Path:
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


def get_run_dir(run_number: Optional[int] = None) -> Path:
    """
    Returns the directory corresponding to a given run number as a Path.
    If no run number is provided, return the current run directory.
    """
    if run_number is None:
        run_number = options.get('current run number')
    return runsdir.joinpath(f"run{run_number}")


def get_time_limit_with_buffer(model_build_time: Optional[int] = 0) -> int:
    time_limit = options.time_limit
    buffer_percent = options["job time limit percent buffer"]
    min_buffer = options["job time limit minimum buffer"]
    time_limit += model_build_time
    time_limit += max(min_buffer, time_limit * buffer_percent / 100)
    return int(ceil(time_limit))


def collect_run_info(run_number: Optional[int] = None):
    this_run_dir = get_run_dir(run_number)
    _read_run_config(this_run_dir)
    started = set()
    model_built = set()
    solver_done = set()  # Does not mean that solver terminated successfully
    finished = set()
    for job in this_run_config.jobs:
        model_name, solver_name = job
        single_job_dir = this_run_dir.joinpath(solver_name, model_name)
        if single_job_dir.joinpath(job_start_filename).exists():
            started.add(job)
        if single_job_dir.joinpath(job_model_built_filename).exists():
            model_built.add(job)
        if single_job_dir.joinpath(job_solve_done_filename).exists():
            solver_done.add(job)
        if single_job_dir.joinpath(job_stop_filename).exists():
            finished.add(job)

    # Total jobs executed
    print(f"{len(started)} of {len(this_run_config.jobs)} jobs executed.")

    # Model build failures
    jobs_with_failed_model_builds = started - model_built
    models_with_failed_builds = {
        model_name: solver_name for model_name, solver_name in jobs_with_failed_model_builds}
    print(f"{len(models_with_failed_builds)} models had failed builds:")
    for model_name, solver_name in models_with_failed_builds.items():
        print(f" - {model_name} (see {solver_name})")

    # Solver execute failures
    solver_fails = defaultdict(list)
    for model_name, solver_name in model_built - solver_done:
        solver_fails[solver_name].append(model_name)
    print(f"{len(solver_fails)} solvers had failed executions:")
    for solver_name, failed_list in solver_fails.items():
        print(f" - {solver_name} ({len(failed_list)} failed): {sorted(failed_list)}")
    # Log the solver failures (Note: this is not the overall errors)
    with this_run_dir.joinpath("solver.failures.log").open('w') as failurelog:
        yaml.safe_dump({k: sorted(v) for k, v in solver_fails.items()}, failurelog, default_flow_style=False)

    # Timeouts and other errors
    print(f"{len(started - finished)} jobs timed out:")
    for model_name, solver_name in started - finished:
        print(f" - {solver_name} {model_name}")

    # Write failures to run info
    this_run_config.jobs_failed = started - solver_done
    # TODO this should be augmented with solvers with bad termination conditions
    this_run_config.jobs_run = started
    _write_run_config(this_run_dir)


def export_to_excel(run_number: Optional[int] = None):
    this_run_dir = get_run_dir(run_number)
    _read_run_config(this_run_dir)
    excel_columns = [
        "time", "model", "solver", "LB", "UB", "elapsed", "iterations",
        "tc", "sense", "soln_gap", "time_to_ok_soln",
        "time_to_soln", "opt_gap", "time_to_opt", "err_msg"]
    rows = []
    for model_name, solver_name in this_run_config.jobs:
        pass


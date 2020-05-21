import stat
import sys
import textwrap
from math import ceil
from pathlib import Path
from typing import Optional, Set

import yaml
from pyutilib.misc import Container

from .model_types import ModelType
from pysperf.model_library import models
from pysperf.solver_library import solvers
from .config import (
    cache_internal_options_to_file, options, run_config_filename, runner_filepath, runsdir, )

this_run_config = Container()


def _write_run_config(this_run_dir: Path):
    config_to_store = Container(**this_run_config)
    if 'jobs_failed' in config_to_store:
        config_to_store.jobs_failed = [(model, solver) for model, solver in config_to_store.jobs_failed]
    if 'jobs_run' in config_to_store:
        config_to_store.jobs_run = [(model, solver) for model, solver in config_to_store.jobs_run]
    with this_run_dir.joinpath(run_config_filename).open('w') as runinfofile:
        yaml.safe_dump(dict(**config_to_store), runinfofile)


def _load_run_config(this_run_dir: Optional[Path] = None):
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


def setup_new_matrix_run(model_set: Set[str] = (),
                         solver_set: Set[str] = (),
                         model_type_set: Set[str] = ()) -> None:
    # Validate inputs
    for model_name in model_set:
        assert model_name in models, f"{model_name} is not in the model library."
    for solver_name in solver_set:
        assert solver_name in solvers, f"{solver_name} is not in the solver library."
    valid_model_names = model_set if model_set else models.keys()
    valid_solver_names = solver_set if solver_set else solvers.keys()
    valid_model_types = {ModelType[mtype] for mtype in model_type_set}
    # create matrix of jobs to run
    jobs = [
        (model_name, solver_name)
        for model_name, model in models.items()
        for solver_name, solver in solvers.items()
        if model.model_type in solver.compatible_model_types
        and model.model_type in valid_model_types
        and model_name in valid_model_names
        and solver_name in valid_solver_names
    ]
    # Set up run configuration file
    this_run_config.clear()  # clear existing configurations
    this_run_config.jobs = jobs
    this_run_config.jobs_to_run = jobs  # This will be different for re-runs
    this_run_config.time_limit = options.time_limit
    # TODO check that other options don't need to be cached here
    # create directories and files
    this_run_dir = _make_new_run_dir()
    print(f"Creating pysperf run{options['current run number']} in directory '{this_run_dir}'.")
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


def setup_redo_matrix_run(run_number: Optional[int] = None,
                          redo_existing: Optional[bool] = False,
                          redo_failed: Optional[bool] = False,
                          model_set: Set[str] = (),
                          solver_set: Set[str] = (),
                          model_type_set: Set[str] = ()) -> None:
    # Validate inputs
    for model_name in model_set:
        assert model_name in models, f"{model_name} is not in the model library."
    for solver_name in solver_set:
        assert solver_name in solvers, f"{solver_name} is not in the solver library."
    valid_model_names = model_set if model_set else models.keys()
    valid_solver_names = solver_set if solver_set else solvers.keys()
    valid_model_types = {ModelType[mtype] for mtype in model_type_set}

    # Handle run number
    if run_number:
        options["current run number"] = run_number
    this_run_dir = get_run_dir(run_number)
    _load_run_config(this_run_dir)
    print(f"Re-executing pysperf run{options['current run number']} in directory '{this_run_dir}'.")

    existing_jobs_to_skip = set() if redo_existing else this_run_config.jobs_run
    failed_jobs_to_skip = set() if redo_failed else this_run_config.jobs_failed

    this_run_config.jobs_to_run = [
        (model_name, solver_name) for (model_name, solver_name) in this_run_config.jobs
        if (model_name, solver_name) not in existing_jobs_to_skip
        and (model_name, solver_name) not in failed_jobs_to_skip
        and models[model_name].model_type in valid_model_types
        and model_name in valid_model_names
        and solver_name in valid_solver_names
    ]

    # Submit jobs for execution
    cache_internal_options_to_file()
    _write_run_config(this_run_dir)


def _make_new_run_dir(run_number: Optional[int] = None) -> Path:
    if run_number:
        # The user specified a run number. Use it.
        next_run_num = run_number
        next_run_dir = f"run{run_number}"
    else:
        # Get the lowest currently available run number.
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

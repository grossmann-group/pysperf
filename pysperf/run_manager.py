import stat
import sys
import textwrap
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
        run_config = {
            "model name": model_name,
            "solver name": solver_name,
            "time limit": options["time limit"],
        }
        with single_run_config_path.open('w') as single_run_config_file:
            yaml.safe_dump(run_config, single_run_config_file)

    # Submit jobs for execution
    with runsdir.joinpath("runs.info.pfcache").open('w') as runsinfofile:
        yaml.safe_dump(dict(**options), runsinfofile)
    with this_run_dir.joinpath("run.queue.pfcache").open('w') as runcache:
        yaml.safe_dump(jobs, runcache)
        # TODO this would be qsub, but here we will add it to an execution queue
    pass


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

"""Global registry"""
from datetime import datetime
from pathlib import Path

import yaml
from pyutilib.misc import Container

# Registries for the models and solvers
models = Container()
solvers = Container()
options = Container()

base_gams_options = [
    'option optcr=0.01;',
    'option optca=0;',
    'option solvelink=5;'
]

# Make output and runs directories, if they do not exist
runsdir = Path(__file__).parent.joinpath("output/runs/")
runsdir.mkdir(exist_ok=True)
outputdir = Path(__file__).parent.joinpath("output/")

# File paths
runner_filepath = Path(__file__).parent.joinpath("pysperf_job_runner.py").resolve()
runner_config_filename = "pysperf_job_runner.config"
job_result_filename = "pysperf_result.log"
job_start_filename = ".job_started.log"
job_stop_filename = ".job_stopped.log"
job_model_built_filename = ".job_model_built.log"
job_solve_done_filename = ".job_solve_done.log"
_internal_config_file = Path(__file__).parent.joinpath('.internal.config.pfcache')
_model_cache_path = Path(__file__).parent.joinpath('model.info.pfcache')
run_config_filename = "run.config.pfdata"

# Load in user and internal options caches
with Path(__file__).parent.joinpath('pysperf.config').open() as _user_config_file:
    _user_options = yaml.safe_load(_user_config_file)
    options.update(_user_options)
if _internal_config_file.exists():
    with _internal_config_file.open('r') as _internal_config_filehandle:
        _internal_options = yaml.safe_load(_internal_config_filehandle)
        if _internal_options:
            options.update(_internal_options)


def cache_internal_options_to_file() -> None:
    _internal_config_options = {k: v for k, v in options.items() if k not in _user_options}
    with _internal_config_file.open('w') as _internal_config_filehandle:
        yaml.safe_dump(_internal_config_options, _internal_config_filehandle)


time_format = "%Y-%m-%d %X.%f"


def get_formatted_time_now():
    return datetime.now().strftime(time_format)

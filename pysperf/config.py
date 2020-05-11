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

outputdir = Path(__file__).parent.joinpath("output/")

with Path(__file__).parent.joinpath('pysperf.config').open() as configfile:
    tester_options = yaml.safe_load(configfile)
    options.update(tester_options)


def get_formatted_time_now():
    time_format = "%Y-%m-%d %X.%f"
    return datetime.now().strftime(time_format)

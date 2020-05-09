"""Global registry"""
from datetime import datetime

import yaml
from pyutilib.misc import Container

# Registries for the models and solvers
models = Container()
solvers = Container()

base_gams_options = [
    'option optcr=0.01;',
    'option optca=0;',
    'option solvelink=5;'
]

with open('pysperf.config') as file:
    tester_options = yaml.safe_load(file)
    time_limit = tester_options["time limit"]
    opt_tol = tester_options["optimality tolerance"]
    ok_tol = tester_options["ok solution tolerance"]


def get_formatted_time_now():
    time_format = "%Y-%m-%d %X.%f"
    return datetime.now().strftime(time_format)

# Main script
from pyutilib.misc import Container

from model_library_tools import compute_model_stats
from run_manager import setup_new_matrix_run, collect_run_info
from torque_run_manager import execute_run
from solver_library_tools import list_solver_capabilities

if __name__ == "__main__":
    from pysperf.model_library import models
    # list_solver_capabilities()
    setup_new_matrix_run()
    execute_run()
    # collect_run_info()


# TODO This module will host all of the argument parsing to support different operations on the test suite
# e.g. setting up runs, restarting runs, re-running failed tests, etc.

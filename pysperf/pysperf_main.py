# Main script
from pyutilib.misc import Container

from model_library_tools import compute_model_stats
from run_manager import setup_matrix_run, collect_run_info
from serial_run_manager import execute_run
from solver_library_tools import list_solver_capabilities

if __name__ == "__main__":
    from pysperf.model_library import models
    compute_model_stats()
    # list_solver_capabilities()
    # setup_matrix_run()
    # execute_run()
    # collect_run_info()

# Main script
from pyutilib.misc import Container

from model_library_tools import compute_model_stats
from config import models
from run_manager import execute_matrix_run
from solver_library_tools import list_solver_capabilities

if __name__ == "__main__":
    from pysperf.models import *  # Imports the models and registers them
    from pysperf.solvers import *  # Imports the solvers and registers them
    compute_model_stats()
    # list_solver_capabilities()
    # execute_matrix_run()

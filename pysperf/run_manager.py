
from pysperf.model_library import models
from pysperf.solver_library import solvers


def execute_matrix_run():
    # create matrix of jobs to run
    jobs = {
        (model_name, solver_name)
        for model_name, model in models.items()
        for solver_name, solver in solvers.items()
        if model.model_type in solver.compatible_model_types
    }
    print(jobs)
    # create directories and files
    # submit job
    pass

"""
This is the runner file called by each job instance for a run.
It loads the job options as recorded in the 'pysperf_runner.config' configuration file,
the correct model and solve, and performs the build and solve.
At the end of the job, it dumps results to the 'pysperf_results.log' file.

At various points in the execution, empty breadcrumb files are generated to indicate progression and status.
These file names are documented in the central configuration file 'config.py'.
"""
from pathlib import Path

import yaml

from config import (
    runner_config_filename, job_model_built_filename, job_result_filename, job_solve_done_filename,
    job_start_filename, job_stop_filename, )
from pysperf import _JobResult, get_formatted_time_now, options


def run_test_case():
    # Load test job configuration
    with open(runner_config_filename) as file:
        runner_options = yaml.safe_load(file)
        model_name = runner_options["model name"]
        solver_name = runner_options["solver name"]
        # Time limit must be updated before solver library import.
        time_limit = runner_options["time_limit"]
        options.time_limit = time_limit
    # Get model and solver objects
    from pysperf.model_library import models
    from pysperf.solver_library import solvers
    test_model = models[model_name]
    test_solver = solvers[solver_name]
    job_result = _JobResult()
    # Build the model
    job_result.model_build_start_time = get_formatted_time_now()
    pyomo_model = test_model.build_function()
    job_result.model_build_end_time = get_formatted_time_now()
    Path(job_model_built_filename).touch()
    # Run the solver
    job_result.solver_start_time = get_formatted_time_now()
    solve_result = test_solver.solve_function(pyomo_model)
    job_result.solver_end_time = get_formatted_time_now()
    Path(job_solve_done_filename).touch()
    # Update results object
    job_result.update(solve_result)
    # Write result to file
    with open(job_result_filename, 'w') as result_file:
        if 'termination_condition' in job_result:
            job_result.termination_condition = str(job_result.termination_condition)
        yaml.safe_dump(dict(**job_result), result_file)


if __name__ == "__main__":
    try:
        Path(job_start_filename).touch()
        run_test_case()
    finally:
        Path(job_stop_filename).touch()

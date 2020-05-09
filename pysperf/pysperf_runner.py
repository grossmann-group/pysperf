

"""
Output directory structure:

- output
    - runs
        - run1
            - GDPopt-LOA
                - MeOH
                    run_script.sh
                    stdout.log
                    stderr.log
                    pyspa_runner.config
                    pyspa_result.log
                    pyspa_case.pytrace
                - 8PP
                - ...
                solver.pytrace
            - BARON-BM
                - MeOH
                - ...
            pyspa_run.pytrace
        - run2
        - ...
    [broad_overview_files]
"""

import yaml

from pysperf import _SingleRunResult, get_formatted_time_now


def run_test_case():
    # Load test run configuration
    with open('pyspa_runner.config') as file:
        runner_options = yaml.safe_load(file)
        model_name = runner_options["model name"]
        solver_name = runner_options["solver name"]
    # Setup run
    from pysperf.model_library import models
    from pysperf.solver_library import solvers
    test_model = models[model_name]
    test_solver = solvers[solver_name]
    run_result = _SingleRunResult()
    # Build the model
    run_result.model_build_start_time = get_formatted_time_now()
    pyomo_model = test_model.build_function()
    run_result.model_build_end_time = get_formatted_time_now()
    # Run the solver
    run_result.solver_start_time = get_formatted_time_now()
    solve_run_result = test_solver.solve_function(pyomo_model)
    run_result.solver_end_time = get_formatted_time_now()
    run_result.update(**solve_run_result)
    # Dump results
    with open('pyspa_result.log', 'w') as result_file:
        yaml.safe_dump(run_result, result_file)
    # Create pytrace file
    pass  # TODO: write this


if __name__ == "__main__":
    run_test_case()

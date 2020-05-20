from collections import defaultdict
from pathlib import Path
from typing import Optional, Tuple

import openpyxl
import pandas
import yaml
from pyomo.environ import SolverStatus, TerminationCondition as pyomo_tc
from pyutilib.misc import Container

from pysperf import _JobResult
from pysperf.model_library import models
from pysperf.solver_library import solvers
from .base_classes import _TestModel, _TestSolver
from .config import (
    cache_internal_options_to_file, job_model_built_filename, job_result_filename, job_solve_done_filename,
    job_start_filename,
    job_stop_filename, options, outputdir, )
from .run_manager import _load_run_config, _write_run_config, get_run_dir, this_run_config


def collect_run_info(run_number: Optional[int] = None):
    if run_number:
        options['current run number'] = run_number
    this_run_dir = get_run_dir(run_number)
    _load_run_config(this_run_dir)
    started = set()
    model_built = set()
    solver_done = set()  # Does not mean that solver terminated successfully
    finished = set()
    for job in this_run_config.jobs:
        model_name, solver_name = job
        single_job_dir = this_run_dir.joinpath(solver_name, model_name)
        if single_job_dir.joinpath(job_start_filename).exists():
            started.add(job)
        if single_job_dir.joinpath(job_model_built_filename).exists():
            model_built.add(job)
        if single_job_dir.joinpath(job_solve_done_filename).exists():
            solver_done.add(job)
        if single_job_dir.joinpath(job_stop_filename).exists():
            finished.add(job)

    # Total jobs executed
    print(f"{len(started)} of {len(this_run_config.jobs)} jobs executed. "
          f"{len(this_run_config.jobs) - len(started)} jobs never executed:")
    for model_name, solver_name in this_run_config.jobs:
        if (model_name, solver_name) not in started:
            print(f" - {model_name} {solver_name}")

    # Model build failures
    jobs_with_failed_model_builds = started - model_built
    models_with_failed_builds = {
        model_name: solver_name for model_name, solver_name in jobs_with_failed_model_builds}
    print(f"{len(models_with_failed_builds)} models had failed builds:")
    for model_name, solver_name in models_with_failed_builds.items():
        print(f" - {model_name} (see {solver_name})")

    # Solver execute failures
    solver_fails = defaultdict(list)
    for model_name, solver_name in model_built - solver_done:
        solver_fails[solver_name].append(model_name)
    print(f"{len(solver_fails)} solvers had failed executions:")
    for solver_name, failed_list in solver_fails.items():
        print(f" - {solver_name} ({len(failed_list)} failed): {sorted(failed_list)}")
    # Log the solver failures (Note: this is not the overall errors)
    with this_run_dir.joinpath("solver.failures.log").open('w') as failurelog:
        yaml.safe_dump({k: sorted(v) for k, v in solver_fails.items()}, failurelog, default_flow_style=False)

    # Timeouts and other errors
    print(f"{len(started - finished)} jobs timed out or still running:")
    for model_name, solver_name in started - finished:
        print(f" - {solver_name} {model_name}")

    # Write sets to files
    this_run_config.jobs_failed = finished - solver_done
    # TODO jobs_failed should be augmented with solvers with bad termination conditions
    this_run_config.jobs_run = finished
    # TODO jobs_run might be adjusted to remove jobs that wrote an empty results object?
    _write_run_config(this_run_dir)
    cache_internal_options_to_file()


def _get_job_result(run_dir: Path, model: str, solver: str):
    with run_dir.joinpath(solver, model, job_result_filename).open('r') as result_file:
        _stored_result = yaml.safe_load(result_file)
    if not _stored_result:
        return _JobResult()
    job_result = _JobResult(**_stored_result)
    if 'termination_condition' in job_result:
        if job_result.termination_condition not in [None, "None"]:
            job_result.termination_condition = pyomo_tc(job_result.termination_condition)
        else:
            job_result.termination_condition = pyomo_tc('unknown')
    if 'pyomo_solver_status' in job_result:
        job_result.pyomo_solver_status = SolverStatus(job_result.pyomo_solver_status)
    return job_result


def export_to_excel(run_number: Optional[int] = None):
    this_run_dir = get_run_dir(run_number)
    _load_run_config(this_run_dir)
    excel_columns = [
        "time", "model", "solver", "LB", "UB", "elapsed", "iterations",
        "tc", "sense", "soln_gap", "time_to_ok_soln",
        "time_to_soln", "opt_gap", "time_to_opt", "err_msg"]
    rows = []
    # Process successfully complete jobs
    for job in this_run_config.jobs_run - this_run_config.jobs_failed:
        model_name, solver_name = job
        test_model = models[model_name]
        test_solver = solvers[solver_name]
        job_data = Container()
        job_data.model = model_name
        job_data.solver = solver_name
        test_result = _get_job_result(this_run_dir, model_name, solver_name)
        if not test_result:
            continue  # TODO This should be unnecessary. We should detect a failure earlier in analysis.
        job_data.time = test_result.model_build_start_time
        job_data.LB = test_result.LB
        job_data.UB = test_result.UB
        job_data.elapsed = test_result.solver_run_time
        job_data.iterations = test_result.get('iterations', None)
        job_data.tc = test_result.termination_condition
        job_data.sense = test_model.objective_sense
        if job_data.tc != 'infeasible':
            job_data.soln_gap, job_data.opt_gap = _calculate_gaps(
                test_model, test_solver, test_result.LB, test_result.UB)
        else:
            job_data.soln_gap, job_data.opt_gap = None, None

        # Times to solution/optimality
        if job_data.soln_gap is not None and job_data.soln_gap <= options.optcr + options['optcr tolerance']:
            job_data.time_to_soln = test_result.solver_run_time
            job_data.time_to_ok_soln = test_result.solver_run_time
        elif job_data.soln_gap is not None and job_data.soln_gap <= options["ok solution tolerance"]:
            job_data.time_to_soln = float('inf')
            job_data.time_to_ok_soln = test_result.solver_run_time
        else:
            job_data.time_to_soln = float('inf')
            job_data.time_to_ok_soln = float('inf')

        if job_data.opt_gap is not None and job_data.opt_gap <= options.optcr + options['optcr tolerance']:
            job_data.time_to_opt = test_result.solver_run_time
        else:
            job_data.time_to_opt = float('inf')

        rows.append(job_data)
    # Use Pandas to export to excel
    df = pandas.DataFrame.from_records(
        rows, columns=excel_columns
    ).replace(  # replace infinity with empty cells
        [float('inf'), float('-inf')], [None, None])
    with pandas.ExcelWriter(str(outputdir.joinpath("results.xlsx"))) as writer:
        df.to_excel(writer, sheet_name="data")
    _autoformat_excel()


def _autoformat_excel():
    # autoformat Excel sheet
    wb = openpyxl.load_workbook(outputdir.joinpath("results.xlsx").open('rb'))
    worksheet = wb.active
    for col in worksheet.columns:
        max_length = 0
        column = col[0].column_letter  # Get the column name
        for cell in col:
            if len(str(cell.value)) > max_length:
                max_length = len(str(cell.value))
        adjusted_width = (max_length + 2) * 1.05
        worksheet.column_dimensions[column].width = adjusted_width
    worksheet.freeze_panes = 'A2'
    wb.save(outputdir.joinpath("results.xlsx").open('wb'))


def _calculate_gaps(test_model: _TestModel, test_solver: _TestSolver, lb: float, ub: float) -> Tuple[float, float]:
    minimizing = test_model.objective_sense == "minimize"
    if lb is None:
        lb = float('-inf')
    if ub is None:
        ub = float('inf')

    library_solution = test_model.get('opt_value', None)
    global_opt_known = True
    if library_solution is None:
        library_solution = test_model.get('best_value')
        global_opt_known = False

    if test_model.model_type not in test_solver.global_for_model_types:
        global_opt_known = False

    # For maximization problems, reverse the sign so that I can write
    # remaining code as if it were minimization.
    solution_value = ub if minimizing else -lb
    lower_bound_value = lb if minimizing else -ub
    correct_solution = library_solution if minimizing else -library_solution

    # If the lower bound is above the upper bound (e.g. due to no-good cuts), then set it to be equal.
    lower_bound_value = solution_value if lower_bound_value > solution_value else lower_bound_value

    soln_gap = abs((solution_value - correct_solution) / correct_solution)
    opt_gap = abs((solution_value - lower_bound_value) / correct_solution) if global_opt_known else None
    return soln_gap, opt_gap

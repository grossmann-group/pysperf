import csv
import textwrap
from datetime import datetime
from typing import Optional

import pyomo.environ as pyo
import yaml

from pysperf.base_classes import _JobResult, InfeasibleExpected
from pysperf.config import outputdir, time_format
from pysperf.model_library import models, requires_model_stats
from pysperf.solver_library import solvers
from pysperf.paver_utils.julian import get_julian_datetime
from pysperf.paver_utils.parse_to_gams import solver_status_to_gams, termination_condition_to_gams_format
from pysperf.run_manager import _load_run_config, get_run_dir, this_run_config


@requires_model_stats
def create_solu_file() -> None:
    """
    Creates the pysperf_models.solu file based on optimal and best-solution-known information for each model.
    """
    with outputdir.joinpath("pysperf_models.solu").open('w') as solufile:
        for test_model in models.values():
            if test_model.opt_value is InfeasibleExpected:
                soln_type, soln_value = "=inf=", ""
            elif test_model.opt_value is not None:
                soln_type, soln_value = "=opt=", test_model.opt_value
            else:
                soln_type, soln_value = "=best=", test_model.best_value
            print(f"{soln_type}\t{test_model.name}\t{soln_value}", file=solufile)
            if test_model.best_dual is not None:
                print(
                    f"=bestdual=\t{test_model.name}\t{test_model.best_dual}", file=solufile)


@requires_model_stats
def create_paver_tracefile(run_number: Optional[int] = None):
    this_run_dir = get_run_dir(run_number)
    _load_run_config(this_run_dir)
    # Create trace file
    trace_header = """\
        * Trace Record Definition
        * GamsSolve
        * InputFileName,ModelType,SolverName,NLP,MIP,JulianDate,Direction
        *  ,NumberOfEquations,NumberOfVariables,NumberOfDiscreteVariables
        *  ,NumberOfNonZeros,NumberOfNonlinearNonZeros,OptionFile
        *  ,ModelStatus,SolverStatus,ObjectiveValue,ObjectiveValueEstimate
        *  ,SolverTime,NumberOfIterations,NumberOfDomainViolations,NumberOfNodes,#empty1
        """
    trace_data = []
    for model_name, solver_name in this_run_config.jobs_run - this_run_config.jobs_failed:
        with this_run_dir.joinpath(solver_name, model_name, "pysperf_result.log").open('r') as resultfile:
            job_result = _JobResult(**yaml.safe_load(resultfile))
        _validate_job_result(job_result)
        test_model = models[model_name]
        test_solver = solvers[solver_name]
        trace_line = [
            model_name,  # Model Name
            'MINLP',  # LP, MIP, NLP, etc.
            solver_name,  # ...
            test_solver.nlp,  # default NLP solver
            test_solver.milp,  # default MIP solver
            get_julian_datetime(datetime.strptime(
                job_result.model_build_start_time, time_format)),  # start day/time of job
            0 if test_model.objective_sense == "minimize" else 1,  # direction 0=min, 1=max
            test_model.constraints,  # total number of equations
            test_model.variables,  # total number of variables
            # total number of discrete variables
            test_model.binary_variables + test_model.integer_variables,
            '',  # 'nznum?',  # number of nonzeros
            '',  # 'nlz?',  # number of nonlinear nonzeros
            0,  # 1= optfile included
            termination_condition_to_gams_format(
                job_result.termination_condition),
            # GAMS model return status - see the GAMS return codes section.
            # GAMS solver return status - see the GAMS return codes section.
            solver_status_to_gams(pyo.SolverStatus.ok),
            job_result.UB,  # value of objective function
            job_result.UB,  # objective function estimate # TODO I think this only works for minimize?
            job_result.solver_run_time,  # resource time used (sec)
            job_result.iterations,  # number of solver iterations
            0,  # dom used
            0,  # nodes used
            '# automatically generated by pysperf'
        ]
        trace_data.append(trace_line)

    with outputdir.joinpath("results.trc").open('w') as tracefile:
        tracefile.write(textwrap.dedent(trace_header))
        tracefile.write('*\n')
        csvwriter = csv.writer(tracefile)
        csvwriter.writerows(trace_data)


def _validate_job_result(job_result: _JobResult):
    if job_result.termination_condition is None or job_result.termination_condition == 'None':
        job_result.termination_condition = pyo.TerminationCondition.unknown
    elif type(job_result.termination_condition) == str:
        job_result.termination_condition = pyo.TerminationCondition(
            job_result.termination_condition)

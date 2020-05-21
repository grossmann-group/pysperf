from pyomo.environ import SolverFactory

from pysperf.base_classes import _JobResult
from pysperf.config import get_base_gams_options_list, options
from pysperf.model_types import ModelType
from pysperf.solver_library_tools import register_solve_function


@register_solve_function(
    name="GDPopt-LOA",
    milp='cplex', nlp='ipopth',
    compatible_model_types={ModelType.GDP, ModelType.DP},
    global_for_model_types={ModelType.cvxGDP, ModelType.DP})
def LOA(pyomo_model):
    job_result = _JobResult()
    pyomo_results = SolverFactory('gdpopt').solve(
        pyomo_model,
        tee=True,
        mip_solver='gams',
        mip_solver_args=dict(solver='cplex', add_options=get_base_gams_options_list()),
        nlp_solver='gams',
        nlp_solver_args=dict(solver='ipopth', add_options=get_base_gams_options_list()),
        minlp_solver='gams',
        minlp_solver_args=dict(solver='dicopt', add_options=get_base_gams_options_list()),
        iterlim=300,
        time_limit=options.time_limit
    )
    job_result.solver_run_time = pyomo_results.solver.timing.total
    job_result.pyomo_solver_status = pyomo_results.solver.status
    job_result.iterations = pyomo_results.solver.iterations
    job_result.termination_condition = pyomo_results.solver.termination_condition
    job_result.LB = pyomo_results.problem.lower_bound
    job_result.UB = pyomo_results.problem.upper_bound
    return job_result


@register_solve_function(
    name="GDPopt-GLOA",
    milp='cplex', nlp='baron',
    compatible_model_types={ModelType.GDP, ModelType.DP},
    global_for_model_types={ModelType.GDP, ModelType.DP})
def GLOA(pyomo_model):
    job_result = _JobResult()
    pyomo_results = SolverFactory('gdpopt').solve(
        pyomo_model,
        tee=True,
        strategy='GLOA',
        mip_solver='gams',
        mip_solver_args=dict(solver='cplex', add_options=get_base_gams_options_list()),
        nlp_solver='gams',
        nlp_solver_args=dict(solver='baron', add_options=get_base_gams_options_list()),
        minlp_solver='gams',
        minlp_solver_args=dict(solver='baron', add_options=get_base_gams_options_list()),
        iterlim=300,
        time_limit=options.time_limit
    )
    job_result.solver_run_time = pyomo_results.solver.timing.total
    job_result.pyomo_solver_status = pyomo_results.solver.status
    job_result.iterations = pyomo_results.solver.iterations
    job_result.termination_condition = pyomo_results.solver.termination_condition
    job_result.LB = pyomo_results.problem.lower_bound
    job_result.UB = pyomo_results.problem.upper_bound
    return job_result


@register_solve_function(
    name="GDPopt-GLOA-DVB",
    milp='cplex', nlp='baron',
    compatible_model_types={ModelType.GDP, ModelType.DP},
    global_for_model_types={ModelType.GDP, ModelType.DP})
def GLOA_with_disjunctive_bounds(pyomo_model):
    job_result = _JobResult()
    pyomo_results = SolverFactory('gdpopt').solve(
        pyomo_model,
        tee=True,
        strategy='GLOA',
        mip_solver='gams',
        mip_solver_args=dict(solver='cplex', add_options=get_base_gams_options_list()),
        nlp_solver='gams',
        nlp_solver_args=dict(solver='baron', add_options=get_base_gams_options_list()),
        minlp_solver='gams',
        minlp_solver_args=dict(solver='baron', add_options=get_base_gams_options_list()),
        iterlim=300,
        calc_disjunctive_bounds=True,
        time_limit=options.time_limit
    )
    job_result.solver_run_time = pyomo_results.solver.timing.total
    job_result.pyomo_solver_status = pyomo_results.solver.status
    job_result.iterations = pyomo_results.solver.iterations
    job_result.termination_condition = pyomo_results.solver.termination_condition
    job_result.LB = pyomo_results.problem.lower_bound
    job_result.UB = pyomo_results.problem.upper_bound
    return job_result


@register_solve_function(
    name="GDPopt-LBB",
    milp='cplex', nlp='baron',
    compatible_model_types={ModelType.GDP, ModelType.DP},
    global_for_model_types={ModelType.GDP, ModelType.DP})
def LBB(pyomo_model):
    job_result = _JobResult()
    pyomo_results = SolverFactory('gdpopt').solve(
        pyomo_model,
        tee=True,
        strategy='LBB',
        mip_solver='gams',
        mip_solver_args=dict(solver='cplex', add_options=get_base_gams_options_list()),
        nlp_solver='gams',
        nlp_solver_args=dict(solver='baron', add_options=get_base_gams_options_list()),
        minlp_solver='gams',
        minlp_solver_args=dict(solver='baron', add_options=get_base_gams_options_list()),
        iterlim=300,
        time_limit=options.time_limit
    )
    job_result.solver_run_time = pyomo_results.solver.timing.total
    job_result.pyomo_solver_status = pyomo_results.solver.status
    job_result.iterations = pyomo_results.solver.iterations
    job_result.termination_condition = pyomo_results.solver.termination_condition
    job_result.LB = pyomo_results.problem.lower_bound
    job_result.UB = pyomo_results.problem.upper_bound
    return job_result

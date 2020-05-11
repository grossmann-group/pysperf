from base_classes import _SingleRunResult
from config import base_gams_options, config
from model_types import ModelType
from pyomo.environ import SolverFactory
from solver_library_tools import register_solve_function


@register_solve_function(
    name="GDPopt-LOA",
    compatible_model_types={ModelType.GDP},
    global_for_model_types={ModelType.cvxGDP})
def LOA(pyomo_model):
    run_result = _SingleRunResult()
    pyomo_results = SolverFactory('gdpopt').solve(
        pyomo_model,
        tee=True,
        mip_solver='gams',
        mip_solver_args=dict(solver='cplex', add_options=base_gams_options),
        nlp_solver='gams',
        nlp_solver_args=dict(solver='ipopth', add_options=base_gams_options),
        minlp_solver='gams',
        minlp_solver_args=dict(solver='dicopt', add_options=base_gams_options),
        iterlim=300,
        time_limit=config.time_limit
    )
    run_result.solver_run_time = pyomo_results.solver.timing.total
    run_result.iterations = pyomo_results.solver.iterations
    run_result.termination_condition = pyomo_results.solver.termination_condition
    run_result.LB = pyomo_results.problem.lower_bound
    run_result.UB = pyomo_results.problem.upper_bound
    return run_result

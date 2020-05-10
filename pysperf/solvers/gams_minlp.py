from base_classes import _SingleRunResult
from config import base_gams_options, time_limit
from model_types import ModelType
from pyomo.environ import SolverFactory
from solver_library_tools import register_GDP_reformulations, register_solve_function


@register_GDP_reformulations
@register_solve_function(
    compatible_model_types={ModelType.MINLP},
    global_for_model_types={ModelType.cvxMINLP})
def DICOPT(pyomo_model):
    run_result = _SingleRunResult()
    pyomo_results = SolverFactory('gams').solve(
        pyomo_model,
        tee=True,
        solver='baron',
        add_options=base_gams_options + [f'option reslim={time_limit};']
    )
    run_result.solver_run_time = pyomo_results.solver.timing.total
    run_result.iterations = pyomo_results.solver.iterations
    run_result.termination_condition = pyomo_results.solver.termination_condition
    run_result.LB = pyomo_results.problem.lower_bound
    run_result.UB = pyomo_results.problem.upper_bound
    return run_result

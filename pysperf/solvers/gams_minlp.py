from pyomo.environ import SolverFactory

from pysperf.base_classes import _JobResult
from pysperf.config import get_base_gams_options_list, options
from pysperf.model_types import ModelType
from pysperf.solver_library_tools import register_GDP_reformulations, register_solve_function


@register_GDP_reformulations
@register_solve_function(
    compatible_model_types={ModelType.MINLP},
    global_for_model_types={ModelType.cvxMINLP})
def DICOPT(pyomo_model):
    job_result = _JobResult()
    pyomo_results = SolverFactory('gams').solve(
        pyomo_model,
        tee=True,
        keepfiles=True,
        solver='baron',
        add_options=get_base_gams_options_list() + [f'option reslim={options.time_limit};']
    )
    job_result.solver_run_time = pyomo_results.solver.user_time
    job_result.pyomo_solver_status = pyomo_results.solver.status
    job_result.termination_condition = pyomo_results.solver.termination_condition
    job_result.LB = pyomo_results.problem.lower_bound
    job_result.UB = pyomo_results.problem.upper_bound
    return job_result

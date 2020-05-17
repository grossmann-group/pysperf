from pyomo.environ import SolverFactory

from pysperf.base_classes import _JobResult
from pysperf.config import base_gams_options, options
from pysperf.model_types import ModelType
from pysperf.solver_library_tools import register_solve_function


@register_solve_function(
    name="GDPopt-LOA",
    compatible_model_types={ModelType.GDP},
    global_for_model_types={ModelType.cvxGDP})
def LOA(pyomo_model):
    job_result = _JobResult()
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
        time_limit=options.time_limit
    )
    job_result.solver_run_time = pyomo_results.solver.timing.total
    job_result.pyomo_solver_status = pyomo_results.solver.status
    job_result.iterations = pyomo_results.solver.iterations
    job_result.termination_condition = pyomo_results.solver.termination_condition
    job_result.LB = pyomo_results.problem.lower_bound
    job_result.UB = pyomo_results.problem.upper_bound
    return job_result

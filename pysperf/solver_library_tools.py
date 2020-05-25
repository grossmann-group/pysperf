import textwrap
from functools import partial
from typing import Callable, Optional, Set

import pandas

from .base_classes import _JobResult, _TestSolver
from .config import _solver_info_log_path, solvers, get_formatted_time_now
from .model_types import ModelType
from pyomo.environ import TransformationFactory, ConcreteModel

# Maps registered solver functions to their names in the library
# when decorator is used.
_name_map = dict()


def register_solver(
        name: str, solve_function: Callable[[ConcreteModel], _JobResult],
        milp: Optional[str] = None, nlp: Optional[str] = None,
        compatible_model_types: Optional[Set[ModelType]] = None,
        global_for_model_types: Optional[Set[ModelType]] = None) -> None:
    if name in solvers:
        raise AttributeError(f"{name} already exists in the solver registry.")
    new_solver = _TestSolver()
    new_solver.name = name
    new_solver.solve_function = solve_function
    new_solver.milp = milp
    new_solver.nlp = nlp
    new_solver.compatible_model_types = compatible_model_types if compatible_model_types else set()
    new_solver.global_for_model_types = global_for_model_types if global_for_model_types else set()
    solvers[name] = new_solver


def register_solve_function(
        name: Optional[str] = None,
        milp: Optional[str] = None, nlp: Optional[str] = None,
        compatible_model_types: Optional[Set[ModelType]] = None,
        global_for_model_types: Optional[Set[ModelType]] = None) -> Callable:
    def anon_decorator(solve_function):
        register_solver(solve_function.__name__, solve_function,
                        milp, nlp,
                        compatible_model_types, global_for_model_types)
        # Necessary to pass information to the register_GDP_reformulations decorator
        _name_map[solve_function] = solve_function.__name__
        return solve_function

    def named_decorator(solve_function):
        register_solver(name, solve_function,
                        milp, nlp,
                        compatible_model_types, global_for_model_types)
        # Necessary to pass information to the register_GDP_reformulations decorator
        _name_map[solve_function] = name
        return solve_function

    if name is None:
        return anon_decorator
    else:
        return named_decorator


def register_GDP_reformulations(mip_solve_function):
    gdp_transformation_methods = {
        'BM': TransformationFactory('gdp.bigm'),
        'HR': TransformationFactory('gdp.chull'),
    }

    base_solver = solvers[_name_map[mip_solve_function]]

    # TODO this can be done better
    mip_to_gdp_map = {
        ModelType.MINLP: ModelType.GDP, ModelType.cvxMINLP: ModelType.cvxGDP,
        ModelType.MILP: ModelType.DP
    }
    gdp_compatible_mtypes = {mip_to_gdp_map[mtype] for mtype in base_solver.compatible_model_types}
    gdp_global_mtypes = {mip_to_gdp_map[mtype] for mtype in base_solver.global_for_model_types}

    def get_solve_function_with_xfrm(xfrm):
        def gdp_solve_function(pyomo_model: ConcreteModel) -> _JobResult:
            job_result = _JobResult()
            job_result.gdp_to_mip_xfrm_start_time = get_formatted_time_now()
            xfrm.apply_to(pyomo_model)
            job_result.gdp_to_mip_xfrm_end_time = get_formatted_time_now()
            mip_job_result = mip_solve_function(pyomo_model)
            job_result.update(mip_job_result)
            return job_result
        return gdp_solve_function

    for xfrm_name, xfrm in gdp_transformation_methods.items():
        register_solver(
            name=base_solver.name + "-" + xfrm_name,
            solve_function=get_solve_function_with_xfrm(xfrm),
            milp=base_solver.milp,
            nlp=base_solver.nlp,
            compatible_model_types=gdp_compatible_mtypes,
            global_for_model_types=gdp_global_mtypes,
        )

    return mip_solve_function


def _get_solver_capability_marker(solver, model_type):
    if model_type in solver.global_for_model_types:
        return 'G'
    elif model_type in solver.compatible_model_types:
        return 'x'
    else:
        return None


def list_solver_capabilities():
    columns = ['name'] + [mtype.name for mtype in ModelType]
    df = pandas.DataFrame.from_records(
        tuple({'name': solver.name,
               **{mtype.name: _get_solver_capability_marker(solver, mtype) for mtype in ModelType}
               } for solver in solvers.values()),
        columns=columns
    ).set_index("name").fillna('.')
    with pandas.option_context(
            'display.max_rows', None, 'display.max_columns', None, 'expand_frame_repr', False
    ), _solver_info_log_path.open('w') as resultsfile:
        print(df, file=resultsfile)
    print(df)
    print(textwrap.dedent("""\
    Legend:
        G - solves model type to global optimality
        X - compatible with model type
    """))

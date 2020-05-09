from functools import wraps
from typing import Callable, Optional

import pandas
from pyutilib.misc import Container

from base_classes import _TestModel
from pyomo.environ import Suffix
from pyomo.util.model_size import build_model_size_report
from config import models


def register_model(
        name: str, build_function: Callable,
        model_type=None, convex=None,
        soln_value=None, opt_value=None, bigM=None) -> None:
    """
    Registers the model in the model library.

    Parameters
    ----------
    name : str
        Registry name for the model.
    build_function
        Function that returns a `pyomo.environ.ConcreteModel` object
    model_type : pyspa.model_types.ModelType, optional
        Model classification (e.g. MINLP)
    convex : bool, optional
        Indicate whether the model is convex
    soln_value: float, optional
        Objective value of best known solution. Either `soln_value` or `opt_value` must be specified.
    opt_value: float, optional
        Objective value of optimal solution. Either `soln_value` or `opt_value` must be specified.
    bigM : float, optional
        Default Big-M parameter value to use.

    """
    if name in models:
        raise AttributeError(f"{name} already exists in the model registry.")
    new_model = _TestModel()
    new_model.name = name
    new_model.build_function = build_function
    new_model.model_type = model_type
    new_model.convex = convex
    new_model.soln_value = soln_value
    new_model.opt_value = opt_value

    # Add default BigM if one was offered
    def build_function_with_BM_suffix(pyomo_model):
        bm_suffix = pyomo_model.component("BigM")
        if bm_suffix is None:
            bm_suffix = pyomo_model.BigM = Suffix()
        bm_suffix[None] = bigM
    new_model.build_function = build_function_with_BM_suffix
    models[name] = new_model


def register_model_builder(
        name: Optional[str] = None, model_type=None, convex: Optional[bool] = None,
        soln_value: Optional[float] = None, opt_value: Optional[float] = None,
        bigM: Optional[float] = None) -> Callable:
    def anon_decorator(build_function):
        register_model(build_function.__name__, build_function, model_type, convex, soln_value, opt_value, bigM)
        return build_function

    def named_decorator(build_function):
        register_model(name, build_function, model_type, convex, soln_value, opt_value, bigM)
        return build_function

    if name is None:
        return anon_decorator
    else:
        return named_decorator


def compute_model_stats():
    reports = [(model.name, model.convex, build_model_size_report(model.build_function()))
               for model in models.values()]
    for name, convex, report in reports:
        report.activated.name = name
        report.activated.convex = convex
    columns = [
        'name',
        'variables', 'binary_variables', 'integer_variables', 'continuous_variables',
        'constraints', 'nonlinear_constraints',
        'disjuncts', 'disjunctions', 'convex',
    ]
    df = pandas.DataFrame.from_records(
        tuple(report.activated for _, report in reports),
        columns=columns
    ).set_index("name")
    with pandas.option_context(
            'display.max_rows', None, 'display.max_columns', None, 'expand_frame_repr', False
    ), open('models.info.log', 'w') as resultsfile:
        print(df, file=resultsfile)
    print(df)




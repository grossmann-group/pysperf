from typing import Callable, Optional

import pyomo.environ as pyo

from .base_classes import _TestModel
from .config import models


def register_model(
        name: str, build_function: Callable,
        model_type=None, convex=None,
        best_value=None, opt_value=None, bigM=None) -> None:
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
    best_value: float, optional
        Objective value of best known solution. Either `best_value` or `opt_value` must be specified.
    opt_value: float, optional
        Objective value of optimal solution. Either `best_value` or `opt_value` must be specified.
    bigM : float, optional
        Default Big-M parameter value to use.
        We inject the BigM `Suffix` and set ``pyomo_model.BigM[None] = bigM``.

    """
    if name in models:
        raise AttributeError(f"{name} already exists in the model registry.")
    new_model = _TestModel()
    new_model.name = name
    new_model.build_function = build_function
    new_model.model_type = model_type
    new_model.convex = convex
    new_model.best_value = best_value
    new_model.opt_value = opt_value

    # Add default BigM if one was offered
    def build_function_with_BM_suffix():
        pyomo_model = build_function()
        bm_suffix = pyomo_model.component("BigM")
        if bm_suffix is None:
            bm_suffix = pyomo_model.BigM = pyo.Suffix()
        bm_suffix[None] = bigM
        return pyomo_model
    if bigM is not None:
        new_model.build_function = build_function_with_BM_suffix
    else:
        new_model.build_function = build_function
    models[name] = new_model


def register_model_builder(
        name: Optional[str] = None, model_type=None, convex: Optional[bool] = None,
        best_value: Optional[float] = None, opt_value: Optional[float] = None,
        bigM: Optional[float] = None) -> Callable:
    def anon_decorator(build_function):
        register_model(build_function.__name__, build_function, model_type, convex, best_value, opt_value, bigM)
        return build_function

    def named_decorator(build_function):
        register_model(name, build_function, model_type, convex, best_value, opt_value, bigM)
        return build_function

    if name is None:
        return anon_decorator
    else:
        return named_decorator



import logging
from math import ceil
from pathlib import Path
from time import monotonic
from typing import Callable, Optional

import pandas
import yaml

from .base_classes import _TestModel
from .config import _model_cache_path, _model_info_log_path, models
from .model_types import ModelType
import pyomo.environ as pyo
from pyomo.util.model_size import build_model_size_report


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


def compute_model_stats():
    models_loaded_from_cache = _load_from_model_stats_cache()

    _failed_model_names = []
    uncached_models = False
    for test_model in models.values():
        if test_model.name in models_loaded_from_cache:
            continue
        # Model is not already in the cache. Compute its statistics.
        print(f"Model '{test_model.name}' is not in the cache. "
              "Building the model and computing its statistics now. "
              "This may take some time for larger models.")
        uncached_models = True
        build_start_time = monotonic()
        try:
            pyomo_model = test_model.build_function()
        except Exception as err:
            print(f"Failed to build {test_model.name} due to exception: {err}.")
            print("Temporarily removing model from library.")
            _failed_model_names.append(test_model.name)
            continue
        build_end_time = monotonic()
        test_model.build_time = int(ceil(build_end_time - build_start_time))
        size_report = build_model_size_report(pyomo_model)
        # update test_model object with information from model size report
        test_model.update(size_report.activated)
        if test_model.model_type is None:
            test_model.model_type = _infer_model_type(test_model)
        # Determine objective sense
        active_obj = next(pyomo_model.component_data_objects(pyo.Objective, active=True))
        test_model.objective_sense = 'minimize' if active_obj.sense == pyo.minimize else 'maximize'

    for failed_model in _failed_model_names:
        del models[failed_model]

    # Cache the model stats
    if uncached_models:
        _cache_model_stats()


def list_model_stats():
    columns = [  # We specify this list so that the columns are ordered
        'name',
        'variables', 'binary_variables', 'integer_variables', 'continuous_variables',
        'constraints', 'nonlinear_constraints',
        'disjuncts', 'disjunctions', 'convex', 'model_type', 'build_time',
    ]
    df = pandas.DataFrame.from_records(
        tuple({key: test_model[key] for key in columns} for test_model in models.values()),
        columns=columns
    ).set_index("name")
    with pandas.option_context(
            'display.max_rows', None, 'display.max_columns', None, 'expand_frame_repr', False
    ), _model_info_log_path.open('w') as resultsfile:
        print(df, file=resultsfile)
        print(df)


def _infer_model_type(test_model):
    if test_model.disjunctions:
        if test_model.nonlinear_constraints:
            if not test_model.convex:
                return ModelType.GDP
            else:
                return ModelType.cvxGDP
        else:
            return ModelType.DP
    else:  # Not disjunctive
        if test_model.nonlinear_constraints and (
                test_model.binary_variables or test_model.integer_variables):
            if not test_model.convex:
                return ModelType.MINLP
            else:
                return ModelType.cvxMINLP
        elif test_model.nonlinear_constraints:
            if not test_model.convex:
                return ModelType.NLP
            else:
                return ModelType.cvxNLP
        elif test_model.binary_variables or test_model.integer_variables:
            return ModelType.MILP
        else:
            return ModelType.LP


def _load_from_model_stats_cache():
    try:
        with _model_cache_path.open('r') as cachefile:
            # Note: should work equally well with json
            cached_models = yaml.safe_load_all(cachefile)
            loaded_model_names = set()
            for test_model in cached_models:
                loaded_model_names.add(test_model['name'])
                if 'model_type' in test_model:
                    test_model['model_type'] = ModelType[test_model['model_type']]
                library_model = models.get(test_model['name'], None)
                if library_model is not None:
                    library_model.update(test_model)
                else:
                    logging.warning(f"Cached model {test_model['name']} not found in library. "
                                    "Cache may be invalid.")
    except FileNotFoundError:
        loaded_model_names = set()
    return loaded_model_names


def _cache_model_stats():
    excluded_keys = {"build_function", "opt_value", "best_value"}
    model_info_to_cache = [{k: v for (k, v) in model.items()
                            if k not in excluded_keys and v is not None}
                           for model in models.values()]
    for test_model in model_info_to_cache:
        test_model['model_type'] = test_model['model_type'].name
    # Note: should work equally well with json
    with _model_cache_path.open('w') as cachefile:
        yaml.safe_dump_all(model_info_to_cache, cachefile)

"""
This file imports `__all__` from the models directory, thus populating the model registry.
"""
import functools
import logging
from functools import partial
from math import ceil
from time import monotonic
from typing import Callable, Optional, Set

import pandas
import pyomo.environ as pyo
import yaml
from pyomo.util.model_size import build_model_size_report

from .config import _model_cache_path, _model_info_log_path, models
from .models import *  # Register all models in the library.

from .model_types import ModelType


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


def compute_model_stats(only_models: Set[str] = ()):
    models_loaded_from_cache = _load_from_model_stats_cache()

    _failed_model_names = []
    uncached_models = False
    for test_model in models.values():
        if test_model.name in models_loaded_from_cache:
            continue
        if only_models and test_model.name not in only_models:
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


def requires_model_stats(orig_func: Optional[Callable] = None, *, only_models: Set[str] = ()) -> Callable:
    """
    Function decorator to ensure that the model statistics are available for the decorated function.

    Parameters
    ----------
    orig_func: Callable
        original function
    only_models: set of str
        If specified, only statistics for these model names will be computed.

    Returns
    -------
    Callable
    """
    if orig_func is None:
        return partial(requires_model_stats, only_models=only_models)

    @functools.wraps(orig_func)
    def wrapper(*args, **kwargs):
        compute_model_stats(only_models=only_models)
        orig_func(*args, **kwargs)
    return wrapper


@requires_model_stats
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

"""
This file imports `__all__` from the models directory, thus populating the model registry.

It also runs 'compute_model_stats()' on the model library.
This can be an expensive operation, if the model info is not already cached.
"""
from .model_library_tools import compute_model_stats
from pysperf.models import *
from .config import models

compute_model_stats()

__all__ = ['models']

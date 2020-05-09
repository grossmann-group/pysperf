"""
This file imports `__all__` from the models directory, thus populating the model registry.
"""

from pysperf.models import *
from config import models

__all__ = ['models']

from enum import Enum, auto, unique
from typing import Set


@unique
class ModelType(Enum):
    GDP = auto()
    DP = auto()
    MINLP = auto()
    NLP = auto()
    MILP = auto()
    LP = auto()

    # Note: "convex" refers to the continuous functions
    cvxGDP = auto()
    cvxMINLP = auto()
    cvxNLP = auto()

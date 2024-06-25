
from enum import Enum


class DependencyType(Enum):
    """ Enum for all kinds of dependencies """
    untracked = 0
    reference = 1
    generative = 2

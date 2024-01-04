from enum import Enum

class BaselineCalcType(Enum):
    NONE = 1 # isn't a calculated baseline product
    PRE_CALCULATED = 2 # Has pre-calculated insarBaseline value
    CALCULATED = 3 # Calculate at run-time
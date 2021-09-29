import dateparser, datetime
import re
from WKTUtils.Input import parse_wkt_util
from asf_search import ASFSession
import http.cookiejar
from typing import Union, List

# Parse and validate a string: "abc".
# Needs to throw on empty strings, so can't use "str()"
def parse_string(v: str) -> str:
    # Convert to string first, so length is checked against only str types:
    try:
        v = f'{v}'
    except ValueError as e: # If this happens, printing v's value would fail too...
        raise ValueError(f"Invalid string: Can't cast {type(v)} to string.") from e
    if len(v) == 0:
        raise ValueError(f'Invalid string: Empty.')
    return v

# Needs to throw if parser returns None, so can't use vanilla datetime parser:
def parse_date(v: Union[str, datetime.datetime]) -> datetime.datetime:
    if isinstance(v, datetime.datetime):
        return v
    d = dateparser.parse(str(v))
    if d is None:
        raise ValueError(f"Invalid date: '{v}'.")
    return d

# Parse and validate a numeric value range, using h() to validate each value: "3-5", "1.1-12.3"
def parse_range(v: list, h: type) -> Union[list, type]:
    if not isinstance(v, list):
        raise ValueError(f'Invalid {h.__name__} range: Must pass in a list. Got {type(v)}.')
    if len(v) != 2:
        raise ValueError(f'Invalid {h.__name__} range: Must have exactly two items. Currently has {len(v)}.')
    if v[0] > v[1]:
        ValueError(f"Invalid {h.__name__} range: Out of order: '{v[0]} > {v[1]}'")
    # Not sure how to typehint this:
    if v[0] == v[1]:
        return v[0]
    return [ h(v[0]), h(v[1]) ]

# Parse and validate a date range: "1991-10-01T00:00:00Z,1991-10-02T00:00:00Z"
def parse_date_range(v: List[Union[str, datetime.datetime]]) -> List[datetime.datetime]:
    return parse_range(v, parse_date)

# Parse and validate an integer range: "3-5"
def parse_int_range(v: List[int]) -> List[int]:
    return parse_range(v, int)

# Parse and validate a float range: "1.1-12.3"
def parse_float_range(v: List[float]) -> List[float]:
    return parse_range(v, float)

# Parse and validate a list of values, using h() to validate each value: "a,b,c", "1,2,3", "1.1,2.3"
def parse_list(v: list, h: type) -> list:
    if not isinstance(v, list):
        raise ValueError(f'Invalid {h.__name__} list: Must pass in a list. Got {type(v)}.')
    try:
        return [h(a) for a in v]
    except ValueError as e:
        raise ValueError(f'Invalid {h.__name__} list: {e}') from e

# Parse and validate a list of strings: "foo,bar,baz"
def parse_string_list(v: List[str]) -> List[str]:
    return parse_list(v, str)

# Parse and validate a list of integers: "1,2,3"
def parse_int_list(v: List[int]) -> List[int]:
    return parse_list(v, int)

# Parse and validate a list of floats: "1.1,2.3,4.5"
def parse_float_list(v: List[float]) -> List[float]:
    return parse_list(v, float)

# Parse and validate a number or a range, using h() to validate each value: "1", "4.5", "3-5", "10.1-13.4"
# Returns whatever type h happens to be... but idk how to type hint that...
def parse_number_or_range(v: Union[list, type], h: type):
    try:
        if isinstance(v, list):
            return parse_range(v, h)
        else:
            return h(v)
    except ValueError as e:
        raise ValueError(f'Invalid {h.__name__} or range: {e}') from e

# Parse and validate a list of numbers or number ranges, using h() to validate each value: "1,2,3-5", "1.1,1.4,5.1-6.7"
def parse_number_or_range_list(v: list, h: type) -> list:
    if not isinstance(v, list):
        raise ValueError(f'Invalid {h.__name__} or range list: Must pass in a list. Got {type(v)}.')
    return [parse_number_or_range(x, h) for x in v]

# Parse and validate a list of integers or integer ranges: "1,2,3-5"
def parse_int_or_range_list(v: list) -> list:
    return parse_number_or_range_list(v, int)

# Parse and validate a list of float or float ranges: "1.0,2.0,3.0-5.0"
def parse_float_or_range_list(v: list) -> list:
    return parse_number_or_range_list(v, float)

# Parse and validate a coordinate list
def parse_coord_list(v: List[float]) -> List[float]:
    if not isinstance(v, list):
        raise ValueError(f'Invalid coord list list: Must pass in a list. Got {type(v)}.')
    for c in v:
        try:
            float(c)
        except ValueError as e:
            raise ValueError(f'Invalid coordinate: {c}') from e
    if len(v) % 2 != 0:
        raise ValueError(f'Invalid coordinate list, odd number of values provided: {v}')
    return v

# Parse and validate a bbox coordinate list
def parse_bbox_list(v: List[float]) -> List[float]:
    try:
        # This also makes sure v is a list:
        v = parse_coord_list(v)
    except ValueError as e:
        raise ValueError(f'Invalid bbox: {e}') from e
    if len(v) != 4:
        raise ValueError(f'Invalid bbox, must be 4 values: {v}')
    return v

# Parse and validate a point coordinate list
def parse_point_list(v: List[float]) -> List[float]:
    try:
        # This also makes sure v is a list:
        v = parse_coord_list(v)
    except ValueError as e:
        raise ValueError(f'Invalid point: {e}') from e
    if len(v) != 2:
        raise ValueError(f'Invalid point, must be 2 values: {v}')
    return v

# Parse a WKT and convert it to a coordinate string
# NOTE: If given an empty ("POINT EMPTY") shape, will return "point:". Should it throw instead?
def parse_wkt(v: str) -> str:
    # The utils library needs this function for repairWKT.
    return parse_wkt_util(v)

def parse_session(*args, **kwargs):
    if len(args) + len(kwargs) == 1:
        if len(args) == 1 and isinstance(args[0], ASFSession):
            return args[0]
        if len(kwargs) == 1 and "asf_session" in kwargs and isinstance(kwargs["asf_session"], ASFSession):
            return kwargs["asf_session"]
    return ASFSession(*args, **kwargs)
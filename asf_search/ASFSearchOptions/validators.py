import dateparser
import datetime

import requests
from typing import Union, Tuple, TypeVar, Callable, List, Type

import math
from shapely import wkt, errors

number = TypeVar('number', int, float)

def parse_string(value: str) -> str:
    """
    Base string validator. Maybe silly, but we can also ensure any constraints needed in the future.
    :param value: The string to validate
    :return: The validated string, with any required modifications
    """
    # Convert to string first, so length is checked against only str types:
    try:
        value = f'{value}'
    except ValueError as exc: # If this happens, printing v's value would fail too...
        raise ValueError(f"Invalid string: Can't cast type '{type(value)}' to string.") from exc
    if len(value) == 0:
        raise ValueError(f'Invalid string: Empty.')
    return value


def parse_float(value: float) -> float:
    """
    Base float validator. Ensures values like Inf are not allowed even though they are valid floats.
    :param value: The float to validate
    :return: The validated float
    """
    try:
        value = float(value)
    except ValueError as exc:
        raise ValueError(f'Invalid float: {value}') from exc
    if math.isinf(value):
        raise ValueError(f'Float values must be finite: got {value}')
    return value


def parse_date(value: Union[str, datetime.datetime]) -> str:
    """
    Base date validator
    :param value: String or datetime object to be validated
    :return: String passed in, if it can successfully convert to Datetime.
    (Need to keep strings like "today" w/out converting them, but throw on "asdf")
    """
    if isinstance(value, datetime.datetime):
        return value
    date = dateparser.parse(str(value))
    if date is None:
        raise ValueError(f"Invalid date: '{value}'.")
    return str(value)


def parse_range(value: Tuple[number, number], h: Callable[[number], number]) -> Tuple[number, number]:
    """
    Base range validator. For our purposes, a range is a tuple with exactly two numeric elements (a, b), requiring a <= b.
    :param value: The range to be validated. Examples: (3, 5), (1.1, 12.3)
    :param h: The validator function to apply to each individual value
    :return: Validated tuple representing the range
    """
    if isinstance(value, tuple):
        if len(value) < 2:
            raise ValueError(f'Not enough values in min/max tuple: {value}')
        if len(value) > 2:
            raise ValueError(f'Too many values in min/max tuple: {value}')
        value = (h(value[0]), h(value[1]))
        if math.isinf(value[0]) or math.isnan(value[0]):
            raise ValueError(f'Expected finite numeric min in min/max tuple, got {value[0]}: {value}')
        if math.isinf(value[1]) or math.isnan(value[1]):
            raise ValueError(f'Expected finite numeric max in min/max tuple, got {value[1]}: {value}')
        if value[0] > value[1]:
            raise ValueError(f'Min must be less than max when using min/max tuples to search: {value}')
        return value
    raise ValueError(f'Invalid range. Expected 2-value numeric tuple, got {type(value)}: {value}')


# Parse and validate a date range: "1991-10-01T00:00:00Z,1991-10-02T00:00:00Z"
def parse_date_range(value: Tuple[Union[str, datetime.datetime], Union[str, datetime.datetime]]) -> Tuple[datetime.datetime, datetime.datetime]:
    return parse_range(value, parse_date)


# Parse and validate an integer range: "3-5"
def parse_int_range(value: Tuple[int, int]) -> Tuple[int, int]:
    return parse_range(value, int)


# Parse and validate a float range: "1.1-12.3"
def parse_float_range(value: Tuple[float, float]) -> Tuple[float, float]:
    return parse_range(value, float)


# Parse and validate a list of values, using h() to validate each value: "a,b,c", "1,2,3", "1.1,2.3"
def parse_list(value: list, h) -> list:
    if not isinstance(value, list):
        value = [value]
    try:
        return [h(a) for a in value]
    except ValueError as exc:
        raise ValueError(f'Invalid {h.__name__} list: {exc}') from exc

# Parse and validate a list of strings: "foo,bar,baz"
def parse_string_list(value: List[str]) -> List[str]:
    return parse_list(value, str)


# Parse and validate a list of integers: "1,2,3"
def parse_int_list(value: List[int]) -> List[int]:
    return parse_list(value, int)


# Parse and validate a list of floats: "1.1,2.3,4.5"
def parse_float_list(value: List[float]) -> List[float]:
    return parse_list(value, float)


def parse_number_or_range(value: Union[list, Tuple[number, number]], h):
    try:
        if isinstance(value, tuple):
            return parse_range(value, h)
        return h(value)
    except ValueError as exc:
        raise ValueError(f'Invalid {h.__name__} or range: {exc}') from exc


# Parse and validate a list of numbers or number ranges, using h() to validate each value: "1,2,3-5", "1.1,1.4,5.1-6.7"
def parse_number_or_range_list(value: list, h) -> list:
    if not isinstance(value, list):
        value = [value]
    return [parse_number_or_range(x, h) for x in value]


# Parse and validate a list of integers or integer ranges: "1,2,3-5"
def parse_int_or_range_list(value: list) -> list:
    return parse_number_or_range_list(value, int)


# Parse and validate a list of float or float ranges: "1.0,2.0,3.0-5.0"
def parse_float_or_range_list(value: list) -> list:
    return parse_number_or_range_list(value, parse_float)


# Parse and validate a coordinate list
def parse_coord_list(value: List[float]) -> List[float]:
    if not isinstance(value, list):
        raise ValueError(f'Invalid coord list list: Must pass in a list. Got {type(value)}.')
    for coord in value:
        try:
            float(coord)
        except ValueError as exc:
            raise ValueError(f'Invalid coordinate: {coord}') from exc
    if len(value) % 2 != 0:
        raise ValueError(f'Invalid coordinate list, odd number of values provided: {value}')
    return value


# Parse and validate a bbox coordinate list
def parse_bbox_list(value: List[float]) -> List[float]:
    try:
        # This also makes sure v is a list:
        value = parse_coord_list(value)
    except ValueError as exc:
        raise ValueError(f'Invalid bbox: {exc}') from exc
    if len(value) != 4:
        raise ValueError(f'Invalid bbox, must be 4 values: {value}')
    return value


# Parse and validate a point coordinate list
def parse_point_list(value: List[float]) -> List[float]:
    try:
        # This also makes sure v is a list:
        value = parse_coord_list(value)
    except ValueError as exc:
        raise ValueError(f'Invalid point: {exc}') from exc
    if len(value) != 2:
        raise ValueError(f'Invalid point, must be 2 values: {value}')
    return value


# Parse a WKT and convert it to a coordinate string
def parse_wkt(value: str) -> str:
    try:
        value = wkt.loads(value)
    except errors.WKTReadingError as exc:
        raise ValueError(f'Invalid wkt: {exc}') from exc
    return wkt.dumps(value)

# Take "requests.Session", or anything that subclasses it:
def parse_session(session: Type[requests.Session]):
    if issubclass(type(session), requests.Session):
        return session
    else:
        raise ValueError(f'Invalid Session: expected ASFSession or a requests.Session subclass. Got {type(session)}')

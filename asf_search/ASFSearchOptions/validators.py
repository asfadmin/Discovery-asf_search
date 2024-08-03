import dateparser
from datetime import datetime, timezone

import requests
from typing import Dict, Union, Tuple, TypeVar, Callable, List, Type, Sequence

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
    except ValueError as exc:  # If this happens, printing v's value would fail too...
        raise ValueError(f"Invalid string: Can't cast type '{type(value)}' to string.") from exc
    if len(value) == 0:
        raise ValueError('Invalid string: Empty.')
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
    if math.isinf(value) or math.isnan(value):
        raise ValueError(f'Float values must be finite: got {value}')
    return value


def parse_date(value: Union[str, datetime]) -> Union[datetime, str]:
    """
    Base date validator
    :param value: String or datetime object to be validated
    :return: String passed in, if it can successfully convert to Datetime.
    (Need to keep strings like "today" w/out converting them, but throw on "asdf")
    """
    if isinstance(value, datetime):
        return _to_utc(value)

    date = dateparser.parse(str(value))
    if date is None:
        raise ValueError(f"Invalid date: '{value}'.")

    return _to_utc(date).strftime('%Y-%m-%dT%H:%M:%SZ')


def _to_utc(date: datetime):
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return date


def parse_range(
    value: Tuple[number, number], h: Callable[[number], number]
) -> Tuple[number, number]:
    """
    Base range validator. For our purposes, a range is a tuple
    with exactly two numeric elements (a, b), requiring a <= b.

    Parameters
    ----------
    value: The range to be validated. Examples: (3, 5), (1.1, 12.3)
    h: The validator function to apply to each individual value

    Returns
    ----------
    Validated tuple representing the range
    """
    if isinstance(value, tuple):
        if len(value) < 2:
            raise ValueError(f'Not enough values in min/max tuple: {value}')
        if len(value) > 2:
            raise ValueError(f'Too many values in min/max tuple: {value}')
        value = (h(value[0]), h(value[1]))
        if math.isinf(value[0]) or math.isnan(value[0]):
            raise ValueError(
                f'Expected finite numeric min in min/max tuple, got {value[0]}: {value}'
            )
        if math.isinf(value[1]) or math.isnan(value[1]):
            raise ValueError(
                f'Expected finite numeric max in min/max tuple, got {value[1]}: {value}'
            )
        if value[0] > value[1]:
            raise ValueError(
                f'Min must be less than max when using min/max tuples to search: {value}'
            )
        return value
    raise ValueError(f'Invalid range. Expected 2-value numeric tuple, got {type(value)}: {value}')


# Parse and validate a date range: "1991-10-01T00:00:00Z,1991-10-02T00:00:00Z"
def parse_date_range(
    value: Tuple[Union[str, datetime], Union[str, datetime]],
) -> Tuple[datetime, datetime]:
    return parse_range(value, parse_date)


# Parse and validate an integer range: "3-5"
def parse_int_range(value: Tuple[int, int]) -> Tuple[int, int]:
    return parse_range(value, int)


# Parse and validate a float range: "1.1-12.3"
def parse_float_range(value: Tuple[float, float]) -> Tuple[float, float]:
    return parse_range(value, float)


# Parse and validate an iterable of values, using h() to validate each value:
# "a,b,c", "1,2,3", "1.1,2.3"
def parse_list(value: Sequence, h) -> List:
    if not isinstance(value, Sequence) or isinstance(value, str):
        value = [value]
    try:
        return [h(a) for a in value]
    except ValueError as exc:
        raise ValueError(f'Invalid {h.__name__} list: {exc}') from exc


def parse_cmr_keywords_list(value: Sequence[Union[Dict, Sequence]]):
    if not isinstance(value, Sequence) or (
        len(value) == 2 and isinstance(value[0], str)
    ):  # in case we're passed single key value pair as sequence
        value = [value]

    for idx, item in enumerate(value):
        if not isinstance(item, tuple) and not isinstance(item, Sequence):
            raise ValueError(
                f'Expected item in cmr_keywords list index {idx} to be tuple pair, '
                f'got value {item} of type {type(item)}'
            )
        if len(item) != 2:
            raise ValueError(
                f'Expected item in cmr_keywords list index {idx} to be of length 2, '
                f'got value {item} of length {len(item)}'
            )

        search_key, search_value = item
        if not isinstance(search_key, str) or not isinstance(search_value, str):
            raise ValueError(
                f'Expected tuple pair of types: '
                f'"{type(str)}, {type(str)}" in cmr_keywords at index {idx}, '
                f'got value "{str(item)}" '
                f'of types: "{type(search_key)}, {type(search_value)}"'
            )

    return value


# Parse and validate an iterable of strings: "foo,bar,baz"
def parse_string_list(value: Sequence[str]) -> List[str]:
    return parse_list(value, parse_string)


# Parse and validate an iterable of integers: "1,2,3"
def parse_int_list(value: Sequence[int]) -> List[int]:
    return parse_list(value, int)


# Parse and validate an iterable of floats: "1.1,2.3,4.5"
def parse_float_list(value: Sequence[float]) -> List[float]:
    return parse_list(value, float)


def parse_number_or_range(value: Union[List, Tuple[number, number], range], h):
    try:
        if isinstance(value, tuple):
            return parse_range(value, h)
        if isinstance(value, range):
            if value.step == 1:
                return [value.start, value.stop]

        return h(value)

    except ValueError as exc:
        raise ValueError(f'Invalid {h.__name__} or range: {exc}') from exc


# Parse and validate an iterable of numbers or number ranges, using h() to validate each value:
# "1,2,3-5", "1.1,1.4,5.1-6.7"
def parse_number_or_range_list(value: Sequence, h) -> List:
    if not isinstance(value, Sequence) or isinstance(value, range):
        value = [value]

    return [parse_number_or_range(x, h) for x in value]


# Parse and validate an iterable of integers or integer ranges: "1,2,3-5"
def parse_int_or_range_list(value: Sequence) -> List:
    return parse_number_or_range_list(value, int)


# Parse and validate an iterable of float or float ranges: "1.0,2.0,3.0-5.0"
def parse_float_or_range_list(value: Sequence) -> List:
    return parse_number_or_range_list(value, parse_float)


# Parse and validate a coordinate list
def parse_coord_list(value: Sequence[float]) -> List[float]:
    if not isinstance(value, Sequence):
        raise ValueError(f'Invalid coord list list: Must pass in an iterable. Got {type(value)}.')
    for coord in value:
        try:
            float(coord)
        except ValueError as exc:
            raise ValueError(f'Invalid coordinate: {coord}') from exc
    if len(value) % 2 != 0:
        raise ValueError(f'Invalid coordinate list, odd number of values provided: {value}')
    return value


# Parse and validate a bbox coordinate list
def parse_bbox_list(value: Sequence[float]) -> List[float]:
    try:
        # This also makes sure v is an iterable:
        value = parse_coord_list(value)
    except ValueError as exc:
        raise ValueError(f'Invalid bbox: {exc}') from exc
    if len(value) != 4:
        raise ValueError(f'Invalid bbox, must be 4 values: {value}')
    return value


# Parse and validate a point coordinate list
def parse_point_list(value: Sequence[float]) -> List[float]:
    try:
        # This also makes sure v is an iterable:
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


# Parse a CMR circle:
#       [longitude, latitude, radius(meters)]
def parse_circle(value: List[float]) -> List[float]:
    value = parse_float_list(value)
    if len(value) != 3:
        raise ValueError(f'Invalid circle, must be 3 values (lat, long, radius). Got: {value}')
    return value


# Parse a CMR linestring:
#       [longitude, latitude, longitude, latitude, ...]
def parse_linestring(value: List[float]) -> List[float]:
    value = parse_float_list(value)
    if len(value) % 2 != 0:
        raise ValueError(
            f'Invalid linestring, must be values of format (lat, long, lat, long, ...). Got: {value}'
        )
    return value


def parse_point(value: List[float]) -> List[float]:
    value = parse_float_list(value)
    if len(value) != 2:
        raise ValueError(f'Invalid point, must be values of format (lat, long). Got: {value}')
    return value


# Parse and validate a coordinate string
def parse_coord_string(value: List):
    value = parse_float_list(value)
    if len(value) % 2 != 0:
        raise ValueError(
            f'Invalid coordinate string, must be values of format (lat, long, lat, long, ...). Got: {value}'
        )
    return value


# Take "requests.Session", or anything that subclasses it:
def parse_session(session: Type[requests.Session]):
    if issubclass(type(session), requests.Session):
        return session
    else:
        raise ValueError(
            'Invalid Session: expected ASFSession or a requests.Session subclass. '
            f'Got {type(session)}'
        )

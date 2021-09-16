import dateparser
import re
from WKTUtils.Input import parse_wkt_util
from asf_search import ASFSession
import http.cookiejar

## List of changes (Added since there's no dif with pulling from SearchAPI):
# Re-wrote parse_string, to always give good error output. Swapped len check to after str cast
# Added type hints
# Rewrote errors in parse_range, to stop nested "Invalid int date: Invalid date: Invalid date: "
# Switched types passed to parse_range, from i.e. parse_int to int. Mainly for error message mentioned up one ^^
# Same changes to 'list' functions as 'range'

# Parse and validate a string: "abc"
def parse_string(v: str) -> str:
    # Convert to string first, so length is checked against only str types:
    try:
        v = f'{v}'
    except ValueError as e: # If this happens, printing v's value would fail too...
        raise ValueError(f"Invalid string. Can't cast {type(v)} to string") from e
    if len(v) == 0:
        raise ValueError(f'Invalid string: Empty string: {v}')
    return v

# Parse and validate an int: "10"
def parse_int(v: int) -> int:
    try:
        return int(v)
    except ValueError as e:
        raise ValueError(f'Invalid int: {v}') from e

# Parse and validate a float: "1.2"
def parse_float(v: float) -> float:
    try:
        return float(v)
    except ValueError as e:
        raise ValueError(f'Invalid number: {v}') from e

# Parse and validate a date: "1991-10-01T00:00:00Z"
def parse_date(v: str) -> str:
    d = dateparser.parse(v)
    if d is None:
        raise ValueError(f'Invalid date: {v}')
    return dateparser.parse(v).strftime('%Y-%m-%dT%H:%M:%SZ')

# Parse and validate a date range: "1991-10-01T00:00:00Z,1991-10-02T00:00:00Z"
def parse_date_range(v: str) -> str:
    dates = v.split(',')
    if len(dates) != 2:
        raise ValueError('Invalid date range: must be two comma-separated dates')
    return f'{parse_date(dates[0])},{parse_date(dates[1])}'

# Parse and validate a numeric value range, using h() to validate each value: "3-5", "1.1-12.3"
def parse_range(v: str, h: type) -> list:
    try:
        v = v.replace(' ', '')
        m = re.search(r'^(-?\d+(\.\d*)?)-(-?\d+(\.\d*)?)$', v)
        if m is None:
            raise ValueError(f"No match found in string '{v}'")
        a = [h(m.group(1)), h(m.group(3))]
        if a[0] > a[1]:
            raise ValueError(f"Range out of order: '{a[0]} > {a[1]}'")
        if a[0] == a[1]:
            a = a[0]
    except ValueError as e:
        raise ValueError(f'Invalid {h.__name__} range: {e}') from e
    return a

# Parse and validate an integer range: "3-5"
def parse_int_range(v: str) -> list:
    return parse_range(v, int)

# Parse and validate a float range: "1.1-12.3"
def parse_float_range(v: str) -> list:
    return parse_range(v, float)

# Parse and validate a list of values, using h() to validate each value: "a,b,c", "1,2,3", "1.1,2.3"
def parse_list(v: str, h: type) -> list:
    try:
        return [h(a) for a in v.split(',')]
    except ValueError as e:
        raise ValueError(f'Invalid {h.__name__} list: {e}') from e

# Parse and validate a list of strings: "foo,bar,baz"
def parse_string_list(v: str) -> list:
    return parse_list(v, str)

# Parse and validate a list of integers: "1,2,3"
def parse_int_list(v: str) -> list:
    return parse_list(v, int)

# Parse and validate a list of floats: "1.1,2.3,4.5"
def parse_float_list(v: str) -> list:
    return parse_list(v, float)

# Parse and validate a number or a range, using h() to validate each value: "1", "4.5", "3-5", "10.1-13.4"
# Returns whatever type h happens to be... but idk how to type hint that...
def parse_number_or_range(v: str, h: type):
    try:
        m = re.search(r'^(-?\d+(\.\d*)?)$', v)
        if m is not None:
            return h(v)
        return parse_range(v, h)
    except ValueError as e:
        raise ValueError(f'Invalid {h.__name__} or range: {e}') from e

# Parse and validate a list of numbers or number ranges, using h() to validate each value: "1,2,3-5", "1.1,1.4,5.1-6.7"
def parse_number_or_range_list(v: str, h: type) -> list:
    v = v.replace(' ', '')
    return [parse_number_or_range(x, h) for x in v.split(',')]

# Parse and validate a list of integers or integer ranges: "1,2,3-5"
def parse_int_or_range_list(v: str) -> list:
    return parse_number_or_range_list(v, int)

# Parse and validate a list of float or float ranges: "1.0,2.0,3.0-5.0"
def parse_float_or_range_list(v: str) -> list:
    return parse_number_or_range_list(v, float)

# Parse and validate a coordinate string
def parse_coord_string(v: str) -> str:
    v = v.split(',')
    for c in v:
        try:
            float(c)
        except ValueError as e:
            raise ValueError(f'Invalid coordinate: {c}') from e
    if len(v) % 2 != 0:
        raise ValueError(f'Invalid coordinate list, odd number of values provided: {v}')
    return ','.join(v)

# Parse and validate a bbox coordinate string
def parse_bbox_string(v: str) -> str:
    try:
        v = parse_coord_string(v)
    except ValueError as e:
        raise ValueError(f'Invalid bbox: {e}') from e
    if len(v.split(',')) != 4:
        raise ValueError(f'Invalid bbox, must be 4 values: {v}')
    return v

# Parse and validate a point coordinate string
def parse_point_string(v: str) -> str:
    try:
        v = parse_coord_string(v)
    except ValueError as e:
        raise ValueError(f'Invalid point: {e}') from e
    if len(v.split(',')) != 2:
        raise ValueError(f'Invalid point, must be 2 values: {v}')
    return v

# Parse a WKT and convert it to a coordinate string
# NOTE: If given an empty ("POINT EMPTY") shape, will return "point:". Should it throw instead?
def parse_wkt(v: str) -> str:
    # The utils library needs this function for repairWKT.
    return parse_wkt_util(v)

def parse_session(*args, **kwargs):

    ## 1) Turn all args into kwargs:
    if len(args) == 0:
        pass
    if len(args) == 1:
        # Check if cookejar:
        if type(args[0]) == http.cookiejar.CookieJar:
            if "cookies" not in kwargs:
                kwargs["cookies"] = args[0]
            else:
                raise ValueError("Passed multiple 'cookies' objects.")
        # Check if session:
        elif type(args[0]) == ASFSession:
            if "asf_session" not in kwargs:
                kwargs["asf_session"] = args[0]
            else:
                raise ValueError("Passed multiple 'asf_session' objects.")
        # Check if token:
        elif type(args[0]) == str:
            if "token" not in kwargs:
                kwargs["token"] = args[0]
            else:
                raise ValueError("Passed multiple 'token' objects.")
        # Else got no clue:
        else:
            raise ValueError(f"Unknown arg: '{args[0]}'.")
    elif len(args) == 2:
        # Check if user/pass:
        if type(args[0]) == str and type(args[1]) == str:
            # This means you can't do half, i.e. parse_session("user", password="password"). Is this okay?
            if "username" not in kwargs and "password" not in kwargs:
                kwargs["username"] = args[0]
                kwargs["password"] = args[1]
        else:
            raise ValueError(f"Unknown args: '{args}'.")
    else: # len(args) > 2:
        raise ValueError()

    ## 2) Parse kwargs to see which session to call:
    # User / Pass:
    if set(["username", "password"]).issubset(kwargs):
        # Make sure you have ONLY one auth method:
        if len(kwargs) == 2:
            return ASFSession().auth_with_creds(kwargs["username"], kwargs["password"])
        else:
            raise ValueError()
    # Token:
    if "token" in kwargs:
        if len(kwargs) == 1:
            return ASFSession().auth_with_token(kwargs["token"])
        else:
            raise ValueError()
    # Cookes:
    if "cookies" in kwargs:
        if len(kwargs) == 1:
            return ASFSession().auth_with_cookiejar(kwargs["cookies"])
        else:
            raise ValueError()
    # Existing session:
    if "asf_session" in kwargs:
        if len(kwargs) == 1:
            return kwargs["asf_session"]
        else:
            raise ValueError()
    raise ValueError("No known auth method found.")

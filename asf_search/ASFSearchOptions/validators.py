import dateparser, datetime
import re
from WKTUtils.Input import parse_wkt_util
from asf_search import ASFSession
import http.cookiejar


# Parse and validate a string: "abc".
# Needs to throw on empty strings, so can't use "str()"
def parse_string(v: str) -> str:
    # Convert to string first, so length is checked against only str types:
    try:
        v = f'{v}'
    except ValueError as e: # If this happens, printing v's value would fail too...
        raise ValueError(f"Invalid string. Can't cast {type(v)} to string") from e
    if len(v) == 0:
        raise ValueError(f'Invalid string: Empty string: {v}')
    return v

# Parse and validate a date: "1991-10-01T00:00:00Z"
# Needs to throw if parser returns None, so can't use vanilla parser:
def parse_date(v: str) -> str:
    if type(v) == datetime.datetime:
        return v
    d = dateparser.parse(v)
    if d is None:
        raise ValueError(f'Invalid date: {v}')
    return d.strftime('%Y-%m-%dT%H:%M:%SZ')

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
    if len(kwargs) == 1:
        if "token" in kwargs:
            return ASFSession().auth_with_token(kwargs["token"])
        if "cookies" in kwargs:
            return ASFSession().auth_with_cookiejar(kwargs["cookies"])
        if "asf_session" in kwargs:
            return kwargs["asf_session"]
    elif len(kwargs) == 2:
        if set(["username", "password"]).issubset(kwargs):
            return ASFSession().auth_with_creds(kwargs["username"], kwargs["password"])
    raise ValueError(f"No known auth method found. {kwargs}")


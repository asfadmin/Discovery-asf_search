from numbers import Number
import pytest

from shapely.wkt import loads
from shapely.ops import orient

from asf_search.WKT.validate_wkt import validate_wkt, _get_clamped_geometry, _get_convex_hull
from asf_search.exceptions import ASFWKTError


def run_test_validate_wkt_invalid_type_error(wkt: str):
    with pytest.raises(ASFWKTError):
        validate_wkt(wkt)


def run_test_validate_wkt_invalid_wkt_error(wkt: str):
    with pytest.raises(ASFWKTError):
        validate_wkt(wkt)


def run_test_validate_wkt_winding_order(wkt: str):
    original_order = loads(wkt)
    valdiated = validate_wkt(original_order.wkt)

    assert valdiated != original_order


def run_test_valdiate_wkt_valid_wkt(wkt: str):
    assert wkt == validate_wkt(wkt).wkt

def run_test_validate_wkt_clamp_geometry(wkt: str, clamped_wkt: str, clamped_count: Number):
    resp = _get_clamped_geometry(loads(wkt))
    assert resp[0].wkt == clamped_wkt
    assert resp[1].report.split(' ')[2] == str(clamped_count)

def run_test_validate_wkt_convex_hull(wkt: str, corrected_wkt: str):
    shape = loads(wkt)
    assert corrected_wkt == _get_convex_hull(shape)[0].wkt 
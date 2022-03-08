import pytest

from shapely.wkt import loads

from asf_search.WKT.validate_wkt import validate_wkt, _get_clamped_geometry
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

def run_test_validate_wkt_clamp_geometry(wkt: str, clamped_wkt: str):
    assert _get_clamped_geometry(loads(wkt)).wkt == clamped_wkt

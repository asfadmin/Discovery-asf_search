import pytest

from shapely.geometry import Polygon
from shapely.wkt import loads

from asf_search.WKT.validate_wkt import validate_wkt
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
    assert wkt == validate_wkt(wkt)
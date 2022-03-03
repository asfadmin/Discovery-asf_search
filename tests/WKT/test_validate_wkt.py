import pytest

from asf_search.WKT.validate_wkt import validate_wkt
from asf_search.exceptions import ASFWKTError

def test_validate_wkt_invalid_type_error():
    with pytest.raises(ASFWKTError):
        validate_wkt('MULTIPOLYGON(((0 0, 0 1, 1 1, 1 0, 0 0), (2 2, 2 3, 3 3, 3 2, 2 2)))')

def test_validate_wkt_invalid_wkt_error():
    with pytest.raises(ASFWKTError):
        validate_wkt('POLYGON((0 0, 0 1, 1 0, 1 1, 0 0))')

def test_validate_wkt_winding_order():
    # with pytest.raises(ASFWKTError):
    original_order = [(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]
    valdiated = validate_wkt('POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))')
    
    original_order.reverse()

    assert list(valdiated.exterior.coords) == original_order
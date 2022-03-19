from numbers import Number
import pytest
from typing import List

from shapely.wkt import loads
from shapely.geometry import Polygon

from asf_search.WKT.validate_wkt import (
    validate_wkt, 
    _get_clamped_geometry, 
    _get_convex_hull, 
    _merge_overlapping_geometry, 
    _counter_clockwise_reorientation,
    _simplify_aoi,
    _get_shape_coords
)
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


def run_test_valdiate_wkt_valid_wkt(wkt: str, validated_wkt: str):
    assert validated_wkt == validate_wkt(wkt).wkt
    assert validated_wkt == validate_wkt(loads(wkt)).wkt

def run_test_validate_wkt_clamp_geometry(wkt: str, clamped_wkt: str, clamped_count: Number):
    resp = _get_clamped_geometry(loads(wkt))
    assert resp[0].wkt == clamped_wkt
    assert resp[1].report.split(' ')[2] == str(clamped_count)

def run_test_validate_wkt_convex_hull(wkt: str, corrected_wkt: str):
    shape = loads(wkt)
    assert corrected_wkt == _get_convex_hull(shape)[0].wkt 

def run_test_validate_wkt_merge_overlapping_geometry(wkt: str, merged_wkt: str):
    shape = loads(wkt)
    
    assert merged_wkt == _merge_overlapping_geometry(shape)[0].wkt

def run_test_validate_wkt_counter_clockwise_reorientation(wkt: str, cc_wkt: str):
    shape = loads(wkt)
    
    assert cc_wkt == _counter_clockwise_reorientation(shape)[0].wkt

def run_test_valdiate_wkt_get_shape_coords(wkt: str, coords: List[Number]):
    shape = loads(wkt)
    shape_coords = [[coord[0], coord[1]] for coord in _get_shape_coords(shape)]

    coords.sort()
    shape_coords.sort()

    assert len(shape_coords) == len(coords)
    assert  shape_coords == coords
    
def test_validate_wkt_simplify_aoi():
    small_polygon = Polygon([[0,0], [0, 0.000004], [0.00004, 0], [0.00004, 0.000004], [0, 0]])
    
    with pytest.raises(ASFWKTError):
        _simplify_aoi(small_polygon, max_depth=0)
    
from numbers import Number
import pytest
from typing import List

from shapely.wkt import loads
from shapely.geometry import Polygon, MultiLineString
from shapely.geometry.base import BaseMultipartGeometry

from asf_search.WKT.validate_wkt import (
    validate_wkt,
    _search_wkt_prep,
    _get_clamped_and_wrapped_geometry, 
    _get_convex_hull, 
    _merge_overlapping_geometry, 
    _counter_clockwise_reorientation,
    _simplify_aoi,
    _get_shape_coords
)
from asf_search.exceptions import ASFWKTError


def run_test_validate_wkt_invalid_wkt_error(wkt: str):
    with pytest.raises(ASFWKTError):
        validate_wkt(wkt)


def run_test_validate_wkt_valid_wkt(wkt: str, validated_wkt: str):
    expected_aoi = loads(validated_wkt)

    assert validate_wkt(wkt).equals(expected_aoi), f"expected, {expected_aoi.wkt}, got {validate_wkt(wkt).wkt}"
    assert validate_wkt(loads(wkt)).equals(expected_aoi)

def run_test_validate_wkt_clamp_geometry(wkt: str, clamped_wkt: str, clamped_count: Number, wrapped_count: Number):
    resp = _get_clamped_and_wrapped_geometry(loads(wkt))
    assert resp[0].wkt == clamped_wkt
    
    if clamped_count > 0:
        assert resp[1][0].report.split(' ')[2] == str(clamped_count)
    
    if wrapped_count > 0:
        assert resp[1][1].report.split(' ')[2] == str(wrapped_count)

def run_test_validate_wkt_convex_hull(wkt: str, corrected_wkt: str):
    shape = loads(wkt)
    assert corrected_wkt == _get_convex_hull(shape)[0].wkt 

def run_test_validate_wkt_merge_overlapping_geometry(wkt: str, merged_wkt: str):
    shape = loads(wkt)
    
    overlapping = _merge_overlapping_geometry(shape)
    if isinstance(overlapping, BaseMultipartGeometry):
        overlapping = overlapping.geoms
    assert overlapping[0].equals(loads(merged_wkt))

def run_test_validate_wkt_counter_clockwise_reorientation(wkt: str, cc_wkt: str):
    shape = loads(wkt)
    
    assert cc_wkt == _counter_clockwise_reorientation(shape)[0].wkt

def run_test_validate_wkt_get_shape_coords(wkt: str, coords: List[Number]):
    shape = loads(wkt)
    shape_coords = [[coord[0], coord[1]] for coord in _get_shape_coords(shape)]

    coords.sort()
    shape_coords.sort()

    assert len(shape_coords) == len(coords)
    assert shape_coords == coords

def run_test_search_wkt_prep(wkt: str):
    if wkt == ' ':
        with pytest.raises(ASFWKTError):
            _search_wkt_prep(None)
        
        return

    shape = loads(wkt)
    ls = _search_wkt_prep(shape)
    assert ls.geometryType() == shape.geometryType()
    assert shape.wkt == wkt
    
def run_test_simplify_aoi(wkt: str, simplified: str, repairs: List[str]):
    shape = loads(wkt)
    resp, shape_repairs = _simplify_aoi(shape)

    assert resp.equals(loads(simplified))

    for idx, repair in enumerate(repairs):
        assert shape_repairs[idx].report.startswith(repair)

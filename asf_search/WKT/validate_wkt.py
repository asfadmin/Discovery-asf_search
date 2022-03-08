from typing import Union
from shapely import wkt
from shapely.geometry.base import BaseGeometry
from shapely.geometry import Polygon, Point, LineString
from shapely.geometry.polygon import orient
from shapely.ops import transform

from asf_search.exceptions import ASFWKTError

def validate_wkt(aoi: Union[str, BaseGeometry]) -> str:
    
    aoi_shape = BaseGeometry()

    if isinstance(aoi, str):
        aoi_shape = wkt.loads(aoi)
    else:
        aoi_shape = wkt.loads(aoi.wkt)

    if not aoi_shape.is_valid:
        aoi_shape = _search_wkt_prep(aoi_shape)

        if not aoi_shape.is_valid:
            raise ASFWKTError(f'WKT string: \"{aoi_shape.wkt}\" is not a valid WKT string')
    
    simplified = _simplify_geometry(aoi_shape)
    
    return simplified
    

    # if simplified.geom_type in ['Point', 'LineString']:
    #     return simplified.wkt
    
    # if isinstance(simplified, Polygon):
    #     return orient(simplified, sign=1.0).wkt
    
    # raise ASFWKTError(f'The provided WKT is not a valid type. Valid WKT types include \"Point\", \"LineString\", \"Polygon\"')

def _search_wkt_prep(shape: BaseGeometry):

    if isinstance(shape, (Point, LineString)):
        return shape

    if isinstance(shape, Polygon):
        return orient(shape, sign=1.0)
    

def _get_clamped_geometry(shape: BaseGeometry):
    return transform(_clamp_coord, shape)

def _simplify_geometry(geometry: BaseGeometry):
    return _get_clamped_geometry(geometry).simplify(0.0001)

def _clamp_coord(x, y, z=None):
    return tuple([x, _clamp(y)])

def _clamp(num):
    return max(-90, min(90, num))
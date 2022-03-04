from shapely import wkt
from shapely.geometry.base import BaseGeometry
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from asf_search.exceptions import ASFWKTError

def validate_wkt(aoi_wkt: str) -> str:
    aoi_shape = wkt.loads(aoi_wkt)
    
    if not aoi_shape.is_valid:
        raise ASFWKTError(f'WKT string: \"{aoi_wkt}\" is not a valid WKT string')
    
    simplified = _simplify_geometry(aoi_shape)

    if simplified.geom_type in ['Point', 'LineString']:
        return simplified.wkt
    
    if isinstance(simplified, Polygon):
        return orient(simplified, sign=1.0).wkt
    
    raise ASFWKTError(f'The provided WKT is not a valid type. Valid WKT types include \"Point\", \"LineString\", \"Polygon\"')


def _simplify_geometry(geometry: BaseGeometry):
    return geometry.simplify(0.0001)

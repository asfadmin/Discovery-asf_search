from numbers import Number
from typing import Union, Tuple
from shapely import wkt
from shapely.geometry.base import BaseGeometry
from shapely.geometry import Polygon, MultiPolygon, Point, MultiPoint, LineString, MultiLineString, GeometryCollection
from shapely.geometry.collection import BaseMultipartGeometry
from shapely.geometry.polygon import orient
from shapely.ops import transform, orient, unary_union
from asf_search.WKT.RepairEntry import RepairEntry

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

    # if isinstance(shape, Polygon):
    if isinstance(shape, BaseMultipartGeometry) :
        output = []
        for geom in shape.geoms:
                if isinstance(geom, Polygon):
                    output.append(orient(geom))
                else:
                    output.append(geom)

        if isinstance(shape, MultiPolygon):
            return MultiPolygon(output)
        if isinstance(shape, MultiLineString):
            return MultiLineString(output)
        if isinstance(shape, MultiPoint):
            return MultiPoint(output)
        if isinstance(shape, GeometryCollection):
            return GeometryCollection(output)
                         
    
    if isinstance(shape, Polygon):
        return orient(shape, sign=1.0)
    
    raise ASFWKTError(f'The provided WKT is not a valid type. Valid WKT types include \"(Multi-)Point\", \"(Multi-)LineString\", \"(Multi-)Polygon\", and \"GeometricCollections\"')


def _simplify_geometry(geometry: BaseGeometry):
    repair_reports = []
    clamped, report = _get_clamped_geometry(geometry)
    return _counter_clockwise_reorientation(
        clamped.simplify(0.0001)
    )

def _merge_overlapping_geometry(geometry: BaseGeometry):
    merge_report = None

    if isinstance(geometry, BaseMultipartGeometry):
        original_amount = len(geometry.geoms)
        merged = unary_union(geometry)
        if isinstance(merged, BaseMultipartGeometry):
            merge_report = RepairEntry("'type': 'OVERLAP_MERGE'", f"'report': {original_amount - len(merged.geoms)} overlapping shapes merged")
        else:
            merge_report = RepairEntry("'type': 'OVERLAP_MERGE'", f"'report': overlapping shapes merged into one")
            merged = merged.simplify(0.0001)
        return merged, merge_report

    return geometry, merge_report

def _counter_clockwise_reorientation(geometry: BaseGeometry):
    return orient(geometry)

def _get_clamped_geometry(shape: BaseGeometry) -> Tuple[BaseGeometry, RepairEntry]:
    coords_clamped = 0
    def _clamp_coord(x, y, z=None):
        clamped = _clamp(y)

        if clamped != y:
            nonlocal coords_clamped
            coords_clamped += 1

        return tuple([x, clamped])
    
    clamped = transform(_clamp_coord, shape)
    
    repairReport = None

    if coords_clamped > 0:
        repairReport = RepairEntry("'type': 'CLAMP'", f"'report': 'Clamped {coords_clamped} value(s) to +/-90 latitude'")

    return (clamped, repairReport)

def _get_convex_hull(geometry: BaseGeometry) -> Tuple[BaseGeometry, RepairEntry]:
    convexEntry = None
    
    if geometry.geom_type not in ['MultiPoint', 'MultiLineString', 'MultiPolygon', 'GeometryCollection']:
        return geometry, None
    
    possible_repair = RepairEntry("'type': 'CONVEX_HULL_INDIVIDUAL'", "'report': 'Unconnected shapes: Convex-halled each INDIVIDUAL shape to merge them together.'")
    return geometry.convex_hull, possible_repair



def _clamp(num):
    return max(-90, min(90, num))

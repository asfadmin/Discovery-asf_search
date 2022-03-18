from numbers import Number
from typing import Union, Tuple, List
from shapely import wkt
from shapely.geometry.base import BaseGeometry
from shapely.geometry import Polygon, MultiPolygon, Point, MultiPoint, LineString, MultiLineString, GeometryCollection
from shapely.geometry.collection import BaseMultipartGeometry
from shapely.geometry.polygon import orient
from shapely.ops import transform, orient, unary_union
from asf_search.WKT.RepairEntry import RepairEntry
from sklearn.neighbors import NearestNeighbors
import numpy as np

from asf_search.exceptions import ASFWKTError


def validate_wkt(aoi: Union[str, BaseGeometry]) -> str:
    """
    Param aoi: the WKT string or Shapely Geometry to validate and prepare for the CMR query
    Validates the given area of interest, and returns a validated and simplified WKT string
    returns: The input AOI's CMR ready WKT string
    """    
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


def _search_wkt_prep(shape: BaseGeometry):

    if isinstance(shape, (Point, LineString)):
        return shape

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


def _simplify_geometry(geometry: BaseGeometry) -> BaseGeometry:
    """
    param geometry: AOI Shapely Geoemetry to be prepped for CMR 
    prepares geometry for CMR, ensuring geometry is: 
        1. Merged, 
        2. convex-halled
        3. clamped +/-90
        4. simplified until its <= 300 points and no closer than 0.00001
        5. Vertices are in counter-clockwise winding order
    returns: geometry prepped for CMR
    """
    merged, merge_report = _merge_overlapping_geometry(geometry)
    convex, convex_report = _get_convex_hull(merged)
    clamped, clamp_report = _get_clamped_geometry(convex)
    simplified, simplified_report = _simplify_aoi(clamped)
    reoriented, reorientation_report = _counter_clockwise_reorientation(simplified)

    repair_reports = [merge_report, convex_report, clamp_report, *simplified_report, reorientation_report]    
    for report in repair_reports:
        if report is not None:
            print(report.report_type)
            print(report.report)

    validated = transform(lambda x, y, z=None: tuple([round(x, 14), round(y, 14)]), reoriented)
    return validated


def _merge_overlapping_geometry(geometry: BaseGeometry) -> Tuple[BaseGeometry, RepairEntry]:
    """
    parameter geometry: geometry to merge
    Performs a unary union overlapping operation of the input geometry, 
    ensuring geometric collections (multipolygon, multipartgeometry, etc)
    are simplied as much as possible before the convex-hull step
    output: merged-overlapping geoemetry
    """
    merge_report = None

    if isinstance(geometry, BaseMultipartGeometry):
        original_amount = len(geometry.geoms)
        if original_amount == 1:
            return geometry

        merged = unary_union(geometry)

        # if there were non-overlapping shapes
        if isinstance(merged, BaseMultipartGeometry):
            unique_shapes = len(merged.geoms)
            merged = orient(unary_union(GeometryCollection([geom.convex_hull for geom in merged.geoms])))
            merge_report = RepairEntry("'type': 'OVERLAP_MERGE'", f"'report': {unique_shapes} non-overlapping shapes merged by their convex-hulls")
        else:
            merge_report = RepairEntry("'type': 'OVERLAP_MERGE'", f"'report': overlapping {original_amount} shapes merged into one")

        return merged, merge_report

    return geometry, merge_report


def _counter_clockwise_reorientation(geometry: Union[Point, LineString, Polygon]):
    """
        param geometry: Shapely geometry to re-orient
        Ensures the geometry coordinates are wound counter-clockwise
        output: counter-clockwise oriented geometry
    """
    reoriented_report = RepairEntry("'type': 'REVERSE'", "Reversed polygon winding order")
    reoriented = orient(geometry)
    
    if isinstance(geometry, Polygon):
        # if the vertice ordering has changed
        if reoriented.exterior.is_ccw != geometry.exterior.is_ccw:
            return reoriented, reoriented_report

    return reoriented, None


def _get_clamped_geometry(shape: BaseGeometry) -> Tuple[BaseGeometry, RepairEntry]:
    """
    param geometry: Shapely geometry to clamp    
    Clamps geometry to +/-90 latitude
    output: clamped shapely geometry
    """
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
    """
    param geometry: geometry to perform possible convex hull operation on
    If the given geometry is a collection of geoemtries, creates a convex-hull encompassing said geometry
    output: convex hull of multi-part geometry, or the original single-shaped geometry 
    """
    if geometry.geom_type not in ['MultiPoint', 'MultiLineString', 'MultiPolygon', 'GeometryCollection']:
        return geometry, None
    
    possible_repair = RepairEntry("'type': 'CONVEX_HULL_INDIVIDUAL'", "'report': 'Unconnected shapes: Convex-halled each INDIVIDUAL shape to merge them together.'")
    return geometry.convex_hull, possible_repair


def _simplify_aoi(shape: Union[Polygon, LineString, Point], 
                  threshold: Number = 0.00001, 
                  max_depth: Number = 10,
                  nearest_neighbor_distance: Number = 0.004
        ) -> Tuple[Union[Polygon, LineString, Point], List[RepairEntry]]:
    """
    param shape: Shapely geometry to simplify
    param threshold: point proximity threshold to merge nearby points of geometry with
    param max_depth: the current depth of the recursive call, defaults to 10
    nearest_neightbor_distance: the nearest neighboring points contained in the input shape  
    Recursively simplifies geometry with increasing threshold, and 
    until there are no more than 300 points and the nearest neighbor distance is no less that 0.004
    output: simplified geometry
    """
    nearest_neighbor_distance = _nearest_neighbor(shape)
    
    if shape.geom_type == 'Point':
        return shape, []

    if _get_shape_coords_len(shape) <= 300 and nearest_neighbor_distance > 0.004:
        return shape, []

    if max_depth == 0:
        raise ASFWKTError(f'WKT string: \"Could not simplify {shape.geom_type} past 300 points\"')

    simplified = shape.simplify(threshold)
    repair = RepairEntry("'type': 'GEOMETRY_SIMPLIFICATION'", f"'report': 'Shape Simplified: shape of {_get_shape_coords_len(shape)} simplified to {_get_shape_coords_len(simplified)} with proximity threshold of {threshold}'")
    output, repairs = _simplify_aoi(simplified, threshold * 5, max_depth - 1, nearest_neighbor_distance)
    return output, [repair, *repairs]


def _clamp(num):
    """Clamps value between -90 and 90"""
    return max(-90, min(90, num))


def _get_shape_coords_len(geometry: BaseGeometry):
    return len(_get_shape_coords(geometry))


def _get_shape_coords(geometry: BaseGeometry):
    """Returns flattened coordinates of input Shapely geometry"""
    if geometry.geom_type == 'Polygon':
        return list(geometry.exterior.coords[:-1])
    
    if geometry.geom_type == 'LineString':
        return list(geometry.coords)
    
    if geometry.geom_type == 'Point':
        return list(geometry.coords)


    return [*_get_shape_coords(geometry.geoms)]
        

def _nearest_neighbor(geometry: BaseGeometry):
    
    def distance(p1, p2):
        lon1, lat1 = p1
        lon2, lat2 = p2
        # Convert to radians:
        lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
        # haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        km = 6367 * c
        return km

    ## getClosestPointDist START:
    points = _get_shape_coords(geometry)
    if len(points) < 2:
        return float("inf")
    nbrs = NearestNeighbors(n_neighbors=2, metric=distance).fit(points)
    distances, indices = nbrs.kneighbors(points)
    distances = distances.tolist()
    #Throw away unneeded data in distances:
    for i, dist in enumerate(distances):
        distances[i] = dist[1]
    return min(distances)
from json import load
from typing import Tuple
import asf_search as asf
from shapely.wkt import loads
from shapely.geometry import shape, GeometryCollection
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union, transform
from asf_search.constants import PLATFORM
def run_test_ASFSearchResults_intersection(wkt: str):
    aoi = asf.validate_wkt(wkt)
    unchanged_aoi = loads(wkt)
    # aoi = GeometryCollection([aoi, loads(wkt)])
    # exclude SMAP products
    platforms = [
                 PLATFORM.AIRSAR, 
                 PLATFORM.ALOS, 
                 PLATFORM.ERS, 
                 PLATFORM.JERS, 
                 PLATFORM.RADARSAT, 
                 PLATFORM.SEASAT, 
                 PLATFORM.SENTINEL1, 
                 PLATFORM.SIRC, 
                 PLATFORM.UAVSAR
                 ]   
    
    def overlap_check(s1: BaseGeometry, s2: BaseGeometry):
        return s1.overlaps(s2) or s1.touches(s2) or s2.distance(s1) <= 0.0015

    for platform in platforms:
        results = asf.geo_search(intersectsWith=wkt, platform=platform, maxResults=250)
    
        for product in results:
            if shape(product.geometry).is_valid:
                product_geom = asf.validate_wkt(shape(product.geometry))
                assert overlap_check(product_geom, aoi) or overlap_check(product_geom, unchanged_aoi), f"OVERLAP FAIL: {product.properties['sceneName']}, {product.geometry} \nproduct: {product_geom.wkt} \naoi: {aoi.wkt}"

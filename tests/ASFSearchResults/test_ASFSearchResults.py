from json import load
import asf_search as asf
from shapely.wkt import loads
from shapely.ops import transform
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from asf_search.constants import PLATFORM
def run_test_ASFSearchResults_intersection(wkt: str):
    aoi = asf.validate_wkt(wkt)
    unchanged_aoi = loads(wkt) # sometimes geometries don't come back with wrapping in mind

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
        return s1.overlaps(s2) or s1.touches(s2) or s2.distance(s1) <= 0.005

    for platform in platforms:
        results = asf.geo_search(intersectsWith=wkt, platform=platform, maxResults=250)
    
        for product in results:
            if shape(product.geometry).is_valid:
                product_geom = asf.validate_wkt(shape(product.geometry))
                original_shape = unchanged_aoi

                # Shapes crossing antimeridian might have coordinates starting from other side
                if unchanged_aoi.bounds[2] < 0 and product_geom.bounds[0] > 0:
                    original_shape = transform(lambda x, y, z=None: tuple([x + 360, y]), unchanged_aoi)

                assert overlap_check(product_geom, aoi) or overlap_check(product_geom, original_shape), f"OVERLAP FAIL: {product.properties['sceneName']}, {product.geometry} \nproduct: {product_geom.wkt} \naoi: {aoi.wkt}"

from json import load
import asf_search as asf
from shapely.wkt import loads
from shapely.geometry import shape
from shapely.ops import unary_union
from asf_search.constants import PLATFORM
def run_test_ASFSearchResults_intersection(wkt: str):
    aoi = loads(wkt)
    validated = asf.validate_wkt(aoi)
    aoi = unary_union([aoi, validated])
    
    # exclude SMAP products
    platforms = [PLATFORM.AIRSAR, 
                 PLATFORM.ALOS, 
                 PLATFORM.ERS, 
                 PLATFORM.JERS, 
                 PLATFORM.RADARSAT, 
                 PLATFORM.SEASAT, 
                 PLATFORM.SENTINEL1, 
                 PLATFORM.SIRC, 
                 PLATFORM.UAVSAR]   
    
    for platform in platforms:
        results = asf.geo_search(intersectsWith=wkt, platform=platform, maxResults=250)
    
        for product in results:
            product_geom = shape(product.geometry)
            assert product_geom.overlaps(aoi) or product_geom.intersects(aoi) or product_geom.contains(aoi) or product_geom.touches(aoi) or product_geom.within(aoi) or aoi.within(product_geom) or aoi.distance(product_geom) <= 0.0015, f"OVERLAP FAIL: {product.properties['sceneName']}, {product.geometry}"

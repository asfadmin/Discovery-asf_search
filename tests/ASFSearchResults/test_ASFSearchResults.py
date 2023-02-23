from typing import Dict, List
import asf_search as asf
from asf_search import ASFSearchResults
import defusedxml.ElementTree as ETree
import json
import shapely.wkt as WKT
import requests
import csv

from shapely.geometry import Polygon
from shapely.wkt import loads
from shapely.ops import transform
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from asf_search.constants import PLATFORM

# when this replaces SearchAPI change values to cached
API_URL = 'https://api.daac.asf.alaska.edu/services/search/param?'

def run_test_output_format(results: ASFSearchResults): 
    #search results are always sorted this way when returned from asf_search.search(), 
    # but not all test case resources are
    results.sort(key=lambda p: (p.properties['stopTime'], p.properties['fileID']), reverse=True)
    product_list_str = ','.join([product.properties['fileID'] for product in results])

    for output_type in ['csv', 'kml', 'metalink', 'jsonlite', 'jsonlite2']:
        expected = get_SearchAPI_Output(product_list_str, output_type)
        if output_type == 'csv':
            check_csv(results, expected)
        if output_type == 'kml':
            check_kml(results, expected)
        elif output_type == 'metalink':
            check_metalink(results, expected)
        elif output_type in ['jsonlite', 'jsonlite2']:
            check_jsonLite(results, expected, output_type)

def check_metalink(results: ASFSearchResults, expected_str: str):
    actual = ''.join([line for line in results.metalink()])
    assert actual == expected_str

def check_kml(results: ASFSearchResults, expected_str: str):
    namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
    placemarks_path = ".//kml:Placemark"
    root = ETree.fromstring(expected_str)
    placemarks = root.findall(placemarks_path, namespaces)

    tags = ['name', 'description', 'styleUrl']
    actual_root = ETree.fromstring(''.join([line for line in results.kml()]))
    actual = actual_root.findall(placemarks_path, namespaces)

    for idx, element in enumerate(placemarks):
        for idy, field in enumerate(element):
            if field.tag.split('}')[-1] in tags:
                expected_el = str(ETree.tostring(field))
                actual_el = str(ETree.tostring(actual[idx][idy]))
                assert expected_el == actual_el
            elif field.tag.split('}')[-1] == 'Polygon':
                expected_coords = get_coordinates_from_kml(ETree.tostring(field))
                actual_coords = get_coordinates_from_kml(ETree.tostring(actual[idx][idy]))
                expected_polygon = Polygon(expected_coords)
                actual_polygon = Polygon(actual_coords)

                assert actual_polygon.equals(expected_polygon)


def get_coordinates_from_kml(data: str):
    namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}

    coords = []
    coords_lon_lat_path = ".//kml:outerBoundaryIs/kml:LinearRing/kml:coordinates"
    root = ETree.fromstring(data)
    
    coordinates_elements = root.findall(coords_lon_lat_path, namespaces)
    for lon_lat_z in coordinates_elements[0].text.split('\n'):
        if len(lon_lat_z.split(',')) == 3:
            lon, lat, _ = lon_lat_z.strip().split(',')
            coords.append([float(lon), float(lat)])

    return coords
    

def check_csv(results: ASFSearchResults, expected_str: str):
    expected = [product for product in csv.reader(expected_str.split('\n')) if product != []]
    actual = [prod for prod in csv.reader(''.join([s for s in results.csv()]).split('\n')) if prod != []]
    
    assert expected.pop(0) == actual.pop(0)

    for idx, product in enumerate(expected):
        assert actual[idx] == product
    pass

def check_jsonLite(results: ASFSearchResults, expected_str: str, output_type: str):
    jsonlite2 = output_type == 'jsonlite2'
    
    expected = json.loads(expected_str)['results']

    if jsonlite2:
        wkt_key = 'w'
        wkt_unwrapped_key = 'wu'
    else:
        wkt_key = 'wkt'
        wkt_unwrapped_key = 'wkt_unwrapped'

    actual = json.loads(''.join(results.jsonlite2() if jsonlite2 else results.jsonlite()))['results']

    for idx, expected_product in enumerate(expected):
        wkt = expected_product.pop(wkt_key)
        wkt_unwrapped = expected_product.pop(wkt_unwrapped_key)
        
        for key in expected_product.keys():
            assert actual[idx][key] == expected_product[key]
        
        assert WKT.loads(actual[idx][wkt_key]).equals(WKT.loads(wkt))
        assert WKT.loads(actual[idx][wkt_unwrapped_key]).equals(WKT.loads(wkt_unwrapped))

def get_SearchAPI_Output(product_list: List[str], output_type: str) -> List[Dict]:
    response = requests.get(API_URL, [('product_list', product_list), ('output', output_type)])
    response.raise_for_status()
    
    expected = response.text
    
    return expected

def run_test_ASFSearchResults_intersection(wkt: str):
    aoi = asf.validate_wkt(wkt)
    unchanged_aoi = loads(wkt) # sometimes geometries don't come back with wrapping in mind

    # exclude SMAP products
    platforms = [
                 PLATFORM.ALOS,
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

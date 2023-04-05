from typing import Dict, List
import asf_search as asf
from asf_search import ASFSearchResults
import defusedxml.ElementTree as DefusedETree
import xml.etree.ElementTree as ETree
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

    results.searchComplete = True
    
    for output_type in ['csv', 'kml', 'metalink', 'jsonlite', 'jsonlite2', 'geojson']:
        expected = get_SearchAPI_Output(product_list_str, output_type)
        if output_type == 'csv':
            check_csv(results, expected)
        if output_type == 'kml':
            check_kml(results, expected)
        elif output_type == 'metalink':
            check_metalink(results, expected)
        elif output_type in ['jsonlite', 'jsonlite2']:
            check_jsonLite(results, expected, output_type)
        elif output_type == 'geojson':
            check_geojson(results)

def check_metalink(results: ASFSearchResults, expected_str: str):
    actual = ''.join([line for line in results.metalink()])
    
    actual_tree = DefusedETree.fromstring(actual)
    expected_tree = DefusedETree.fromstring(expected_str)
    
    canon_actual = ETree.canonicalize(DefusedETree.tostring(actual_tree), strip_text=True)
    canon_expected = ETree.canonicalize(DefusedETree.tostring(expected_tree), strip_text=True)
    
    assert canon_actual == canon_expected

def check_kml(results: ASFSearchResults, expected_str: str):
    namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
    placemarks_path = ".//kml:Placemark"
    expected_root = DefusedETree.fromstring(expected_str)
    expected_placemarks = expected_root.findall(placemarks_path, namespaces)

    actual_root = DefusedETree.fromstring(''.join([block for block in results.kml()]))
    actual_placemarks = actual_root.findall(placemarks_path, namespaces)
    
    # Check polygons for equivalence (asf-search starts from a different pivot)
    # and remove them from the kml so we can easily compare the rest of the placemark data
    for expected_placemark, actual_placemark in zip(expected_placemarks, actual_placemarks):
        expected_polygon = expected_placemark.findall('./*')[-1]
        actual_polygon = actual_placemark.findall('./*')[-1]
        
        expected_coords = get_coordinates_from_kml(DefusedETree.tostring(expected_polygon))
        actual_coords = get_coordinates_from_kml(DefusedETree.tostring(actual_polygon))
        
        assert Polygon(expected_coords).equals(Polygon(actual_coords))
        
        expected_placemark.remove(expected_polygon)
        actual_placemark.remove(actual_polygon)
        
    # Get canonicalize xml strings so minor differences are normalized
    actual_canon = ETree.canonicalize( DefusedETree.tostring(actual_root), strip_text=True)
    expected_canon = ETree.canonicalize( DefusedETree.tostring(expected_root), strip_text=True)
    
    assert actual_canon == expected_canon


def get_coordinates_from_kml(data: str):
    namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}

    coords = []
    coords_lon_lat_path = ".//kml:outerBoundaryIs/kml:LinearRing/kml:coordinates"
    root = DefusedETree.fromstring(data)
    
    coordinates_elements = root.findall(coords_lon_lat_path, namespaces)
    for lon_lat_z in coordinates_elements[0].text.split('\n'):
        if len(lon_lat_z.split(',')) == 3:
            lon, lat, _ = lon_lat_z.strip().split(',')
            coords.append([float(lon), float(lat)])

    return coords
    

def check_csv(results: ASFSearchResults, expected_str: str):
    expected = [product for product in csv.reader(expected_str.split('\n')) if product != []]
    # actual = [prod for prod in csv.reader(''.join([s for s in results.csv()]).split('\n')) if prod != []]
    
    expected = csv.DictReader(expected_str.split('\n'))
    actual = csv.DictReader([s for s in results.csv()])
    
    for actual_row, expected_row in zip(actual, expected):
        actual_dict = dict(actual_row)
        expected_dict = dict(expected_row)
        
        for key in expected_dict.keys():
            if expected_dict[key] in ['None', None, '']:
                assert actual_dict[key] in ['None', None, '']
            else:
                try:
                    expected_value = float(expected_dict[key])
                    actual_value = float(actual_dict[key])
                    assert expected_value == actual_value, \
                        f"expected \'{expected_dict[key]}\' for key \'{key}\', got \'{actual_dict[key]}\'"
                except ValueError:
                    assert expected_dict[key] == actual_dict[key], \
                        f"expected \'{expected_dict[key]}\' for key \'{key}\', got \'{actual_dict[key]}\'"
 
 
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

def check_geojson(results: ASFSearchResults):
    expected = results.geojson()
    actual = asf.export.results_to_geojson(results)
    
    assert json.loads(''.join(actual)) == expected
    
def get_SearchAPI_Output(product_list: List[str], output_type: str) -> List[Dict]:
    response = requests.get(API_URL, [('product_list', product_list), ('output', output_type)])
    response.raise_for_status()
    
    expected = response.text
    
    return expected

def run_test_ASFSearchResults_intersection(wkt: str):
    wrapped, unwrapped, _ = asf.validate_wkt(wkt)
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
                product_geom_wrapped, product_geom_unwrapped, _ = asf.validate_wkt(shape(product.geometry))
                original_shape = unchanged_aoi

                assert overlap_check(product_geom_wrapped, wrapped) or overlap_check(product_geom_wrapped, original_shape), f"OVERLAP FAIL: {product.properties['sceneName']}, {product.geometry} \nproduct: {product_geom_wrapped.wkt} \naoi: {wrapped.wkt}"

from ast import Lambda
from itertools import product
from typing import Dict, List
from asf_search import ASFSearchResults
import xml.etree.ElementTree as ETree
import os
import json
import shapely.wkt as WKT
import requests
import csv
API_URL = 'https://api.daac.asf.alaska.edu/services/search/param?' #product_list='

# ref = S1B_IW_SLC__1SDV_20210102T032031_20210102T032058_024970_02F8C3_C081-SLC
def run_test_output_format(results: ASFSearchResults, output_type: str, expected_file: str):
    expected_format = expected_file.split('.').pop()
    product_list_str = ','.join([product.properties['fileID'] for product in results])
    expected = get_SearchAPI_Output(product_list_str, output_type)
    base_path = os.path.join(os.getcwd(), 'tests', 'yml_tests', 'Resources/')
    with open(os.path.join(base_path, expected_file), 'r') as f:
        data = f.read()

    if expected_format == 'csv':
        results_csv = results.csv()
        check_csv(results, expected)
    elif expected_format == 'kml':
        results_kml = results.kml()
        check_kml(results, data)
    elif expected_format == 'metalink':
        results_metalink = results.metalink()
    elif expected_format == 'json':
        results_jsonlite = results.jsonlite()
        check_jsonLite(results, expected, output_type)

    pass

def check_kml(results: ASFSearchResults, expected_str: str):
    namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
    xpath = ".//kml:Placemark/kml:name"
    root = ETree.fromstring(expected_str)
    placemarks = root.findall(xpath, namespaces)
    for idx, element in enumerate(placemarks):
        assert element.text == results[idx].properties['sceneName']

def check_csv(results: ASFSearchResults, expected: str):
    expected = [product for product in csv.reader(expected.split('\n')) if product != []][1:]
    for idx, product in enumerate([prod for prod in csv.reader(results.csv()) if prod != []][1:]):
        assert expected[idx] == product
        # print(expected)
    pass

def check_jsonLite(results: ASFSearchResults, expected: str, output_type: str):
    expected = json.loads(expected)['results']
    sort_key = 'gn' if output_type == 'jsonlite2' else 'productID'
    # expected = json.loads(expected_str)['results']
    expected.sort(key=lambda product: product[sort_key])

    if expected:
        if 'wkt' in expected[0].keys():
            wkt_key = 'wkt'
            wkt_unwrapped_key = 'wkt_unwrapped'
            jsonlite2 = False
        else:
            wkt_key = 'w'
            wkt_unwrapped_key = 'wu'
            jsonlite2 = True

    actual = json.loads(''.join(results.jsonlite2() if jsonlite2 else results.jsonlite()))['results']
    actual.sort(key=lambda product: product[sort_key])

    for idx, expected_product in enumerate(expected):
        wkt = expected_product.pop(wkt_key)
        wkt_unwrapped = expected_product.pop(wkt_unwrapped_key)
        
        for key in expected_product.keys():
            assert  actual[idx][key] == expected_product[key]
        
        assert WKT.loads(actual[idx][wkt_key]).equals(WKT.loads(wkt))
        assert WKT.loads(actual[idx][wkt_unwrapped_key]).equals(WKT.loads(wkt_unwrapped))

#
def get_SearchAPI_Output(product_list: List[str], output_type: str) -> List[Dict]:
    response = requests.get(API_URL, [('product_list', product_list), ('output', output_type)])
    response.raise_for_status()
    
    expected = response.text
    
    return expected
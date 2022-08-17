from typing import List
from asf_search import ASFSearchResults
import xml.etree.ElementTree as ETree
import os
import json
import shapely.wkt as WKT
# ref = S1B_IW_SLC__1SDV_20210102T032031_20210102T032058_024970_02F8C3_C081-SLC
def run_test_output_format(results: ASFSearchResults, expected_file: str):
    expected_format = expected_file.split('.').pop()

    base_path = os.path.join(os.getcwd(), 'tests', 'yml_tests', 'Resources/')
    with open(os.path.join(base_path, expected_file), 'r') as f:
        data = f.read()

    if expected_format == 'csv':
        results_csv = results.csv()
    elif expected_format == 'kml':
        results_kml = results.kml()
        check_kml(results, data)
    elif expected_format == 'metalink':
        results_metalink = results.metalink()
    elif expected_format == 'json':
        results_jsonlite = results.jsonlite()
        check_jsonLite(results, data)

    pass

def check_kml(results: ASFSearchResults, expected_str: str):
    namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
    xpath = ".//kml:Placemark/kml:name"
    root = ETree.fromstring(expected_str)
    placemarks = root.findall(xpath, namespaces)
    for idx, element in enumerate(placemarks):
        assert element.text == results[idx].properties['sceneName']

def check_jsonLite(results: ASFSearchResults, expected_str: str):
    # isjsonlite2 = expected_format.split('_')[-1] == "jsonlite2.json"

    expected = json.loads(expected_str)['results']

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

    for idx, expected_product in enumerate(expected):
        wkt = expected_product.pop(wkt_key)
        wkt_unwrapped = expected_product.pop(wkt_unwrapped_key)
        
        for key in expected_product.keys():
            assert  actual[idx][key] == expected_product[key]
        
        assert WKT.loads(actual[idx][wkt_key]).equals(WKT.loads(wkt))
        assert WKT.loads(actual[idx][wkt_unwrapped_key]).equals(WKT.loads(wkt_unwrapped))

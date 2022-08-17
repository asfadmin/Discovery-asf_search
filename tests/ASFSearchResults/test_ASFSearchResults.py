from asf_search import ASFSearchResults
import xml.etree.ElementTree as ETree
import os

# ref = S1B_IW_SLC__1SDV_20210102T032031_20210102T032058_024970_02F8C3_C081-SLC
def run_test_output_format(results: ASFSearchResults, expected_file: str):
    expected_format = expected_file.split('.').pop()

    base_path = os.path.join(os.getcwd(), 'tests', 'yml_tests', 'Resources/')
    with open(os.path.join(base_path, expected_file), 'r') as f:
        data = f.read()

    if expected_format == 'csv':
        results_csv = results.csv()
    if expected_format == 'jsonlite':
        results_jsonlite = results.jsonlite()
    if expected_format == 'jsonlite2':
        results_jsonlite2 = results.jsonlite2()
    if expected_format == 'kml':
        results_kml = results.kml()
        check_kml(results, data)
    if expected_format == 'metalink':
        results_metalink = results.metalink()

    pass

def check_kml(results: ASFSearchResults, expected_str: str):
    namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
    xpath = ".//kml:Placemark/kml:name"
    root = ETree.fromstring(expected_str)
    placemarks = root.findall(xpath, namespaces)
    for idx, element in enumerate(placemarks):
        assert element.text == results[idx].properties['sceneName']

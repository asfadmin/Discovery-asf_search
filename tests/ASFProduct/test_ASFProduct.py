import logging
import pytest
import unittest

from asf_search import ASFProduct, ASFSearchResults, ASFSearchOptions, FileDownloadType
from unittest.mock import patch
from shapely.geometry import shape
from shapely.ops import orient

import requests

def run_test_ASFProduct(product_json):
    if product_json is None:
        product = ASFProduct()
        geojson = product.geojson()
        assert geojson['type'] == 'Feature'
        assert geojson['geometry'] == {'coordinates': None, 'type': 'Polygon'}
        for val in geojson['properties'].values():
            assert val is None

        return

    opts = product_json.pop('opts', None)
    product = ASFProduct(product_json, opts)

    geojson = product.geojson()
    
    if geojson['geometry']['coordinates'] is not None:
        expected_shape = orient(shape(product_json['geometry']))
        output_shape = orient(shape(geojson['geometry'])) 
        assert(output_shape.equals(expected_shape))
    elif product.meta != {}:
        assert product.properties == product_json['properties']
        assert product.geometry == product_json['geometry']

    assert(product.umm == product_json["umm"])
    assert(product.meta == product_json["meta"])

def run_test_stack(reference, pre_processed_stack, processed_stack):
    product = ASFProduct(reference)
    
    with patch('asf_search.baseline_search.search') as search_mock:
        temp = ASFSearchResults([ASFProduct(prod) for prod in pre_processed_stack])
        for idx, prod in enumerate(temp):
            prod.baseline = pre_processed_stack[idx]['baseline']
        search_mock.return_value = temp
        stack = product.stack()


        stack = [
            product for product in stack if product.properties['temporalBaseline'] != None and product.properties['perpendicularBaseline'] != None
            ]

        for(idx, secondary) in enumerate(stack):
            
            if(idx > 0):
                assert(secondary.properties['temporalBaseline'] >= stack[idx - 1].properties['temporalBaseline'])
            
            assert(secondary.properties['temporalBaseline'] == processed_stack[idx]['properties']['temporalBaseline'])
            assert(secondary.properties['perpendicularBaseline'] == processed_stack[idx]['properties']['perpendicularBaseline'])

def run_test_product_get_stack_options(reference, options):
    product = ASFProduct(reference)
    expected_options = dict(ASFSearchOptions(**options))

    product_options = dict(product.get_stack_opts())
    assert product_options == dict(expected_options)

def run_test_ASFProduct_download(reference, filename, filetype, additional_urls):
    product = ASFProduct(reference)
    product.properties['additionalUrls'] = additional_urls
    with patch('asf_search.ASFSession.get') as mock_get:
        resp = requests.Response()
        resp.status_code = 200
        mock_get.return_value = resp
        resp.iter_content = lambda chunk_size: []
            
        with patch('builtins.open', unittest.mock.mock_open()) as m:    
            if filename != None and (
                (filetype == FileDownloadType.ADDITIONAL_FILES and len(additional_urls) > 1) 
                or filetype == FileDownloadType.ALL_FILES
            ):
                with pytest.warns(Warning):
                    product.download('./', filename=filename, fileType=filetype)
            else:
                product.download('./', filename=filename, fileType=filetype)
from typing import Union, Iterable, Tuple, Dict
from asf_search.ASFSearchResults import ASFSearchResults
from ..search.search import ASFProduct

from .fixtures.ASFProduct_fixtures import *

def test_ASFProduct_Geojson_EmptyResponse() -> None:
    empty_response = {"geometry": {}, "properties": {}}
    product = ASFProduct(empty_response)

    geojson = product.geojson()

    assert(geojson['type'] == 'Feature')
    assert(geojson['geometry'] == {})
    assert(geojson['properties'] == {})

def test_ASFProduct_Geo_Search(basic_response):
    geographic_response = basic_response
    product = ASFProduct(geographic_response)

    geojson = product.geojson()
    assert(geojson['geometry'] == geographic_response['geometry'])
    assert(geojson['properties'] == geographic_response['properties'])
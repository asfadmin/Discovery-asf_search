from ..search.search import ASFProduct, ASFSearchResults

from .fixtures.ASFProduct_fixtures import *
from .fixtures.baseline_search_fixtures import s1_search_response, s1_baseline_stack
from unittest.mock import patch
class Test_ASFProduct:
    def test_ASFProduct_Geojson_EmptyResponse(self):
        empty_response = {"geometry": {}, "properties": {}}
        product = ASFProduct(empty_response)

        geojson = product.geojson()

        assert(geojson['type'] == 'Feature')
        assert(geojson['geometry'] == {})
        assert(geojson['properties'] == {})

    def test_ASFProduct_Geo_Search(self, basic_response):
        geographic_response = basic_response
        product = ASFProduct(geographic_response)

        geojson = product.geojson()
        assert(geojson['geometry'] == geographic_response['geometry'])
        assert(geojson['properties'] == geographic_response['properties'])
    
    def test_stack(self, s1_search_response, s1_baseline_stack):
        product = ASFProduct(s1_search_response[0])
        
        with patch('asf_search.baseline_search.search') as search_mock:
            search_mock.return_value = ASFSearchResults(map(lambda prod: ASFProduct(prod), s1_baseline_stack))
            stack = product.stack()
            
            assert(len(stack) == 4)
            for(idx, secondary) in enumerate(stack):
                assert(secondary.properties['temporalBaseline'] >= 0)
                
                if(idx > 0):
                    assert(secondary.properties['temporalBaseline'] >= stack[idx].properties['temporalBaseline'])

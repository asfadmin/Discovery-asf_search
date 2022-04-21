from asf_search.search.search import ASFProduct, ASFSearchResults
from unittest.mock import patch

def run_test_ASFProduct_Geo_Search(geographic_response):
    product = ASFProduct(geographic_response)

    geojson = product.geojson()
    assert(geojson['geometry'] == geographic_response['geometry'])
    assert(geojson['properties'] == geographic_response['properties'])

def run_test_stack( reference, s1_baseline_stack):
    product = ASFProduct(reference)
    
    with patch('asf_search.baseline_search.search') as search_mock:
        search_mock.return_value = ASFSearchResults(map(ASFProduct, s1_baseline_stack))
        stack = product.stack()
        
        for(idx, secondary) in enumerate(stack):
            if(idx > 0):
                assert(secondary.properties['temporalBaseline'] >= stack[idx - 1].properties['temporalBaseline'])

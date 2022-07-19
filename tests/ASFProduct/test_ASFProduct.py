from asf_search.search.search import ASFProduct, ASFSearchResults, ASFSearchOptions
from unittest.mock import patch
from shapely.geometry import shape
from shapely.ops import orient
def run_test_ASFProduct_Geo_Search(geographic_response):
    opts = geographic_response.pop('opts', None)
    product = ASFProduct(geographic_response, opts)

    geojson = product.geojson()
    expected_shape = orient(shape(geographic_response['geometry']))
    output_shape = orient(shape(geojson['geometry'])) 

    assert(output_shape.equals(expected_shape))
    assert(product.umm == geographic_response["umm"])
    assert(product.meta == geographic_response["meta"])

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
from copy import deepcopy
from unittest.mock import patch
from asf_search import product_search, search
from asf_search.exceptions import ASFBaselineError, ASFSearchError
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.search.search import ASFProduct
from asf_search.search.baseline_search import get_stack_opts, stack_from_id, stack_from_product
from asf_search.baseline.stack import calculate_temporal_baselines, get_default_product_type
from asf_search.constants import PLATFORM
import pytest

def run_test_get_preprocessed_stack_params(product):
    reference = ASFProduct(product)
    params = get_stack_opts(reference)

    original_properties = product['properties']
    
    assert(params.processingLevel == [get_default_product_type(product['properties']['sceneName'])])
    assert(params.insarStackId == original_properties['insarStackId'])
    assert(len(dict(params)) == 2)
    

def run_test_get_unprocessed_stack_params(product):
    reference = ASFProduct(product)
    params = get_stack_opts(reference)

    original_properties = product['properties']
    assert(original_properties['polarization'] in params.polarization)
    assert(['VV', 'VV+VH'] == params.polarization)
    assert(len(dict(params)) == 7)

def run_get_stack_opts_invalid_insarStackId(product):
    invalid_reference = ASFProduct(product)
    
    invalid_reference.properties['insarStackId'] = '0'

    with pytest.raises(ASFBaselineError):
        get_stack_opts(invalid_reference)
    
def run_test_get_stack_opts_invalid_platform_raises_error(product):
    invalid_reference = ASFProduct(product)
    invalid_reference.properties['platform'] = None
    
    with pytest.raises(ASFBaselineError):
        get_stack_opts(invalid_reference)
    
def run_test_calc_temporal_baselines(reference, stack):
    reference = ASFProduct(reference)
    stack = ASFSearchResults([ASFProduct(product) for product in stack])
    stackLength = len(stack)

    calculate_temporal_baselines(reference, stack)

    assert(len(stack) == stackLength)
    for secondary in stack:
        assert('temporalBaseline' in secondary.properties)

def run_test_stack_from_product(reference, stack):
    reference = ASFProduct(reference)

    with patch('asf_search.baseline_search.search') as search_mock:
        search_mock.return_value = ASFSearchResults([ASFProduct(product) for product in stack])  

        stack = stack_from_product(reference)

        for (idx, secondary) in enumerate(stack):
            if(idx > 0):
                assert(secondary.properties['temporalBaseline'] >= stack[idx - 1].properties['temporalBaseline'])

def run_test_stack_from_id(stack_id: str, reference, stack):
        temp = deepcopy(stack)

        with patch('asf_search.baseline_search.product_search') as mock_product_search:
            mock_product_search.return_value = ASFSearchResults([ASFProduct(product) for product in stack])
        
            if not stack_id:    
                with pytest.raises(ASFSearchError):
                    stack_from_id(stack_id)
            else:
                with patch('asf_search.baseline_search.search') as search_mock:
                    search_mock.return_value = ASFSearchResults([ASFProduct(product) for product in temp])   

                    returned_stack = stack_from_id(stack_id)
                    assert(len(returned_stack) == len(stack))

                    for (idx, secondary) in enumerate(returned_stack):
                        if(idx > 0):
                            assert(secondary.properties['temporalBaseline'] >= stack[idx - 1]["properties"]['temporalBaseline'])

def run_test_stack_response_properties(reference_id: str):
    reference = product_search(product_list=reference_id)[0]
    
    stack_opts = get_stack_opts(reference)
    
    stack_results = search(opts=stack_opts)
    
    is_sentinel = reference.properties in [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B]
    
    platforms = [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B] if reference.properties in [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B] else [reference.properties['platform']]
    for product in stack_results:
        if is_sentinel:
            assert product.properties['beamModeType'] in stack_opts.beamMode
            assert product.properties['flightDirection'] == stack_opts.flightDirection
            assert product.properties['polarization'] in stack_opts.polarization
            assert product.properties['processingLevel'] in stack_opts.processing_level
            assert product.properties['pathNumber'] in stack_opts.relativeOrbit
            assert product.properties['platform'] in platforms
        else:
            assert product.properties['insarStackId'] == reference.properties['insarStackId']
            assert product.properties['platform'] == reference.properties['platform']
            # assert product.properties['']
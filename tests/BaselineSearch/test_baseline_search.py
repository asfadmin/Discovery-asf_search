from unittest.mock import patch
from asf_search.exceptions import ASFBaselineError, ASFSearchError
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.search.search import ASFProduct
from asf_search.search.baseline_search import calc_temporal_baselines, get_stack_params, stack_from_id, stack_from_product
import pytest

def run_test_get_preprocessed_stack_params(product):
    reference = ASFProduct(product)
    params = get_stack_params(reference)

    original_properties = product['properties']
    assert(params['processingLevel'] == [original_properties['processingLevel']])
    assert(params['insarStackId'] == original_properties['insarStackId'])
    assert(len(params) == 2)
    

def run_test_get_unprocessed_stack_params(product):
    reference = ASFProduct(product)
    params = get_stack_params(reference)

    original_properties = product['properties']
    assert(original_properties['polarization'] in params['polarization'])
    assert(['VV', 'VV+VH'] == params['polarization'])
    assert(len(params) == 7)

def run_get_stack_params_invalid_insarStackId(product):
    invalid_reference = ASFProduct(product)
    
    invalid_reference.properties['insarStackId'] = '0'

    with pytest.raises(ASFBaselineError):
        get_stack_params(invalid_reference)
    
def run_test_get_stack_params_invalid_platform_raises_error(product):
    invalid_reference = ASFProduct(product)
    invalid_reference.properties['platform'] = None
    
    with pytest.raises(ASFBaselineError):
        get_stack_params(invalid_reference)
    
def run_test_calc_temporal_baselines(reference, stack):
    reference = ASFProduct(reference)
    stack = ASFSearchResults(map(ASFProduct, stack))
    stackLength = len(stack)

    calc_temporal_baselines(reference, stack)

    assert(len(stack) == stackLength)
    for secondary in stack:
        assert('temporalBaseline' in secondary.properties)

def run_test_stack_from_product(reference, stack):
    reference = ASFProduct(reference)

    with patch('asf_search.baseline_search.search') as search_mock:
        search_mock.return_value = ASFSearchResults(map(ASFProduct, stack))    

        stack = stack_from_product(reference)

        for (idx, secondary) in enumerate(stack):
            if(idx > 0):
                assert(secondary.properties['temporalBaseline'] >= stack[idx - 1].properties['temporalBaseline'])

def run_test_stack_from_id(stack_id: str, reference, stack):
    
        with patch('asf_search.baseline_search.product_search') as mock_product_search:
            mock_product_search.return_value = ASFSearchResults(map(ASFProduct, stack))
        
            if not stack_id:    
                with pytest.raises(ASFSearchError):
                    stack_from_id(stack_id)
            else:
                with patch('asf_search.baseline_search.search') as search_mock:
                    search_mock.return_value = ASFSearchResults(map(ASFProduct, stack))    

                    returned_stack = stack_from_id(stack_id)
                    assert(len(returned_stack) == len(stack))

                    for (idx, secondary) in enumerate(returned_stack):
                        if(idx > 0):
                            assert(secondary.properties['temporalBaseline'] >= stack[idx - 1]["properties"]['temporalBaseline'])

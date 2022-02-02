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
    stack = ASFSearchResults(map(lambda product: ASFProduct(product), stack))
    stackLength = len(stack)

    calc_temporal_baselines(reference, stack)

    assert(len(stack) == stackLength)
    for secondary in stack:
        assert(secondary.properties['temporalBaseline'] >= 0)

def run_test_stack_from_product(reference, stack):
    reference = ASFProduct(reference)

    with patch('asf_search.baseline_search.search') as search_mock:
        search_mock.return_value = ASFSearchResults(map(lambda product: ASFProduct(product), stack))    

        stack = stack_from_product(reference)

        assert(len(stack) == 4)
        for (idx, secondary) in enumerate(stack):
            assert(secondary.properties['temporalBaseline'] >= 0)

            if(idx > 0):
                assert(secondary.properties['temporalBaseline'] >= stack[idx].properties['temporalBaseline'])

def run_test_stack_from_id(stack_id: str):
    with patch('asf_search.baseline_search.product_search') as empty_product_search:
        empty_product_search.return_value = []
        stack_from_id(stack_id)
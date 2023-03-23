from typing import List
from numbers import Number
from asf_search.baseline.stack import find_new_reference, get_baseline_from_stack, get_default_product_type, valid_state_vectors
from asf_search import ASFProduct, ASFSearchResults
import pytest
def run_test_find_new_reference(stack: List, output_index: Number) -> None:
    """
    Test asf_search.baseline.stack.find_new_reference
    """
    
    if stack == []:
        assert(find_new_reference(stack) == None)
    else:
        products = [ASFProduct(product) for product in stack]
        for idx, product in enumerate(products):
            product = clear_baseline(stack[idx], product)
        assert find_new_reference(products).properties['sceneName'] == stack[output_index]['properties']['sceneName']
        
def run_test_get_default_product_type(product: ASFProduct, product_type: str) -> None:
    assert get_default_product_type(product) == product_type
    
def run_test_get_baseline_from_stack(reference, stack, output_stack, error):
    reference = ASFProduct(reference)
    stack = ASFSearchResults([ASFProduct(product) for product in stack])
    
    if error == None:
        stack, warnings = get_baseline_from_stack(reference, stack)
        
        keys = ['sceneName', 'perpendicularBaseline', 'temporalBaseline']

        for idx, product in enumerate(stack):
            for key in keys:
                assert product.properties[key] == output_stack[idx]['properties'][key]
        
        return
    
    with pytest.raises(ValueError):
        for product in stack:
            if product.baseline.get('insarBaseline', False):
                product.baseline = {}
            else:
                product.baseline['stateVectors']['positions'] = {}
                product.baseline['stateVectors']['velocities'] = {}
        reference.baseline = {}
        get_baseline_from_stack(reference=reference, stack=stack)


def run_test_valid_state_vectors(reference, output):
    if reference != None:
        product = ASFProduct(reference)
        clear_baseline(reference, product)
        assert output == valid_state_vectors(product)
        return
    
    with pytest.raises(ValueError):
        valid_state_vectors(reference)

def clear_baseline(resource, product: ASFProduct):
# Baseline values can be restored from UMM in asfProduct constructor, 
# this erases them again if the resource omitted them from the product
    if resource['baseline'].get('stateVectors', False).get('positions', False) == {}:
        product.baseline['stateVectors']['positions'] = {}
        product.baseline['stateVectors']['velocities'] = {}
    
    return product

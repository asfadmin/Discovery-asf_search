from typing import List
from numbers import Number
from asf_search.baseline.stack import find_new_reference, get_default_product_type
from asf_search import ASFProduct

def run_test_find_new_reference(stack: List, output_index: Number) -> None:
    """
    Test asf_search.baseline.stack.find_new_reference
    """
    
    if stack == []:
        assert(find_new_reference(stack) == None)
    else:
        assert find_new_reference([ASFProduct(product) for product in stack]).properties['sceneName'] == stack[output_index]['properties']['sceneName']
        
def run_test_get_default_product_type(scene_name: str, product_type: str) -> None:
    assert get_default_product_type(scene_name) == product_type
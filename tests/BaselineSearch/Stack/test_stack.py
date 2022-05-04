from asf_search.baseline.stack import find_new_reference
from asf_search import ASFProduct

def run_test_find_new_reference(stack, output_index) -> None:
    """
    Test asf_search.baseline.stack.find_new_reference
    """
    
    if stack == []:
        assert(find_new_reference(stack) == None)
    else:
        assert find_new_reference([ASFProduct(product) for product in stack]).properties['sceneName'] == stack[output_index]['properties']['sceneName']
from typing import List
from numbers import Number
from asf_search.baseline.stack import find_new_reference, get_baseline_from_stack
from asf_search import ASFProduct, ASFSearchResults, ASFSession, ASFStackableProduct
from asf_search.search.search_generator import as_ASFProduct

import pytest


def run_test_find_new_reference(stack: List, output_index: Number) -> None:
    """
    Test asf_search.baseline.stack.find_new_reference
    """

    if stack == []:
        assert find_new_reference(stack) is None
    else:
        products = [as_ASFProduct(product, ASFSession()) for product in stack]
        for idx, product in enumerate(products):
            product = clear_baseline(stack[idx], product)
        assert (
            find_new_reference(products).properties['sceneName']
            == stack[output_index]['properties']['sceneName']
        )


def run_test_get_default_product_type(product: ASFStackableProduct, product_type: str) -> None:
    assert product.get_default_baseline_product_type() == product_type


def run_test_get_baseline_from_stack(reference, stack, output_stack, error):
    reference = as_ASFProduct(reference, ASFSession())
    stack = ASFSearchResults([as_ASFProduct(product, ASFSession()) for product in stack])

    if error is None:
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
    if reference is not None:
        product = as_ASFProduct(reference, ASFSession())
        clear_baseline(reference, product)
        assert output == product.is_valid_reference()
        return


def clear_baseline(resource, product: ASFProduct):
    # Baseline values can be restored from UMM in asfProduct constructor,
    # this erases them again if the resource omitted them from the product
    if stateVectors := resource['baseline'].get('stateVectors'):
        if stateVectors.get('positions') == {}:
            product.baseline = {'stateVectors': {'positions': {}, 'velocities': {}}}

    return product

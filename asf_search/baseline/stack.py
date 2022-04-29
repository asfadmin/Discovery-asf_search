from typing import List
import dateparser
# from SearchAPI.CMR.Translate import translate_params, input_fixer
# from SearchAPI.CMR.Query import CMRQuery
from .calc import calculate_perpendicular_baselines
from asf_search import ASFProduct, granule_search

precalc_datasets = ['AL', 'R1', 'E1', 'E2', 'J1']

def get_baseline_from_stack(reference: str, stack: List[ASFProduct]):
    warnings = None

    if len(stack) == 0:
        raise ValueError('No products found matching stack parameters')

    reference, stack, warnings = check_reference(reference, stack)
    stack = [product for product in stack if not product.properties['processingLevel'].lower().startswith('metadata')]
    stack = calculate_temporal_baselines(reference, stack)

    if get_platform(reference) in precalc_datasets:
        stack = offset_perpendicular_baselines(reference, stack)
    else:
        stack = calculate_perpendicular_baselines(reference, stack)

    return stack, warnings

def valid_state_vectors(product: ASFProduct):
    if product is None:
        raise ValueError('Attempting to check state vectors on None, this is fatal')
    for key in ['postPosition', 'postPositionTime', 'prePosition', 'postPositionTime']:
        if key not in product.properties['baseline']['stateVectors']['positions'] or product.properties['baseline']['stateVectors']['positions'][key] == None:
            return False
    return True

def find_new_reference(stack: List[ASFProduct]):
    for product in stack:
        if valid_state_vectors(product):
            return product.properties['sceneName']
    return None

def check_reference(reference: str, stack: List[ASFProduct]):
    warnings = None
    if reference not in [product.properties['sceneName'] for product in stack]: # Somehow the reference we built the stack from is missing?! Just pick one
        reference = stack[0].properties['sceneName']
        warnings = [{'NEW_REFERENCE': 'A new reference scene had to be selected in order to calculate baseline values.'}]

    for product in stack:
        if product.properties['sceneName'] == reference:
            reference_product = product

    if get_platform(reference) in precalc_datasets:
            if 'insarBaseline' not in reference_product:
                raise ValueError('No baseline values available for precalculated dataset')
    else:
        if not valid_state_vectors(reference_product): # the reference might be missing state vectors, pick a valid reference, replace above warning if it also happened
            reference = find_new_reference(stack)
            if reference is None:
                raise ValueError('No valid state vectors on any scenes in stack, this is fatal')
            warnings = [{'NEW_REFERENCE': 'A new reference had to be selected in order to calculate baseline values.'}]

    return reference, stack, warnings

def get_platform(reference: str):
    return reference[0:2].upper()

def get_default_product_type(reference: str):
    if get_platform(reference) in ['AL']:
        return 'L1.1'
    if get_platform(reference) in ['R1', 'E1', 'E2', 'J1']:
        return 'L0'
    if get_platform(reference) in ['S1']:
        return 'SLC'
    return None

def calculate_temporal_baselines(reference: str, stack: List[ASFProduct]):
    for product in stack:
        if product.properties['sceneName'] == reference:
            reference_start = dateparser.parse(product.properties['startTime'])
            break
    for product in stack:
        if product.properties['sceneName'] == reference:
            product.properties['temporalBaseline'] = 0
        else:
            start = dateparser.parse(product.properties['startTime'])
            product.properties['temporalBaseline'] = (start - reference_start).days
    return stack

def offset_perpendicular_baselines(reference: str, stack: List[ASFProduct]):
    for product in stack:
        if product.properties['sceneName'] == reference:
            reference_offset = float(product.properties['insarBaseline'])
            break
    for product in stack:
        if product.properties['sceneName'] == reference:
            product.properties['perpendicularBaseline'] = 0
        else:
            product.properties['perpendicularBaseline'] = round(float(product.properties['insarBaseline']) - reference_offset)
    return stack

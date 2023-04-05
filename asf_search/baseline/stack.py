from dateutil.parser import parse
import pytz
from .calc import calculate_perpendicular_baselines
from asf_search import ASFProduct, ASFSearchResults

precalc_datasets = ['AL', 'R1', 'E1', 'E2', 'J1']

def get_baseline_from_stack(reference: ASFProduct, stack: ASFSearchResults):
    warnings = None

    if len(stack) == 0:
        raise ValueError('No products found matching stack parameters')
    stack = [product for product in stack if not product.properties['processingLevel'].lower().startswith('metadata') and product.baseline != None]
    reference, stack, warnings = check_reference(reference, stack)
    
    stack = calculate_temporal_baselines(reference, stack)

    if get_platform(reference.properties['sceneName']) in precalc_datasets:
        stack = offset_perpendicular_baselines(reference, stack)
    else:
        stack = calculate_perpendicular_baselines(reference.properties['sceneName'], stack)

    return ASFSearchResults(stack), warnings

def valid_state_vectors(product: ASFProduct):
    if product is None:
        raise ValueError('Attempting to check state vectors on None, this is fatal')
    for key in ['postPosition', 'postPositionTime', 'prePosition', 'postPositionTime']:
        if key not in product.baseline['stateVectors']['positions'] or product.baseline['stateVectors']['positions'][key] == None:
            return False
    return True

def find_new_reference(stack: ASFSearchResults):
    for product in stack:
        if valid_state_vectors(product):
            return product
    return None

def check_reference(reference: ASFProduct, stack: ASFSearchResults):
    warnings = None
    if reference.properties['sceneName'] not in [product.properties['sceneName'] for product in stack]: # Somehow the reference we built the stack from is missing?! Just pick one
        reference = stack[0]
        warnings = [{'NEW_REFERENCE': 'A new reference scene had to be selected in order to calculate baseline values.'}]

    if get_platform(reference.properties['sceneName']) in precalc_datasets:
            if 'insarBaseline' not in reference.baseline:
                raise ValueError('No baseline values available for precalculated dataset')
    else:
        if not valid_state_vectors(reference): # the reference might be missing state vectors, pick a valid reference, replace above warning if it also happened
            reference = find_new_reference(stack)
            if reference == None:
                raise ValueError('No valid state vectors on any scenes in stack, this is fatal')
            warnings = [{'NEW_REFERENCE': 'A new reference had to be selected in order to calculate baseline values.'}]

    return reference, stack, warnings

def get_platform(reference: str):
    return reference[0:2].upper()

def get_default_product_type(product: ASFProduct):
    scene_name = product.properties['sceneName']
    
    if get_platform(scene_name) in ['AL']:
        return 'L1.1'
    if get_platform(scene_name) in ['R1', 'E1', 'E2', 'J1']:
        return 'L0'
    if get_platform(scene_name) in ['S1']:
        if product.properties['processingLevel'] == 'BURST':
            return 'BURST'
        return 'SLC'
    return None

def calculate_temporal_baselines(reference: ASFProduct, stack: ASFSearchResults):
    """
    Calculates temporal baselines for a stack of products based on a reference scene and injects those values into the stack.

    :param reference: The reference product from which to calculate temporal baselines.
    :param stack: The stack to operate on.
    :return: None, as the operation occurs in-place on the stack provided.
    """
    reference_time = parse(reference.properties['startTime'])
    if reference_time.tzinfo is None:
        reference_time = pytz.utc.localize(reference_time)

    for secondary in stack:
        secondary_time = parse(secondary.properties['startTime'])
        if secondary_time.tzinfo is None:
            secondary_time = pytz.utc.localize(secondary_time)
        secondary.properties['temporalBaseline'] = (secondary_time.date() - reference_time.date()).days
    
    return stack

def offset_perpendicular_baselines(reference: ASFProduct, stack: ASFSearchResults):
    reference_offset = float(reference.baseline['insarBaseline'])
    
    for product in stack:
            product.properties['perpendicularBaseline'] = round(float(product.baseline['insarBaseline']) - reference_offset)
    
    return stack

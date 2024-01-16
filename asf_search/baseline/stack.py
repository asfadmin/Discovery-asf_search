from dateutil.parser import parse
import pytz

from .calc import calculate_perpendicular_baselines
from asf_search import ASFProduct, ASFSearchResults

def get_baseline_from_stack(reference: ASFProduct, stack: ASFSearchResults):
    warnings = None

    if len(stack) == 0:
        raise ValueError('No products found matching stack parameters')
    stack = [product for product in stack if not product.properties['processingLevel'].lower().startswith('metadata') and product.baseline != None]
    
    reference, stack, warnings = check_reference(reference, stack)
    
    stack = calculate_temporal_baselines(reference, stack)

    if reference.baseline_type == ASFProduct.BaselineCalcType.PRE_CALCULATED:
        stack = offset_perpendicular_baselines(reference, stack)
    else:
        stack = calculate_perpendicular_baselines(reference.properties['sceneName'], stack)

    return ASFSearchResults(stack), warnings

def find_new_reference(stack: ASFSearchResults):
    for product in stack:
        if product.is_valid_reference():
            return product
    return None

def check_reference(reference: ASFProduct, stack: ASFSearchResults):
    warnings = None
    if reference.properties['sceneName'] not in [product.properties['sceneName'] for product in stack]: # Somehow the reference we built the stack from is missing?! Just pick one
        reference = stack[0]
        warnings = [{'NEW_REFERENCE': 'A new reference scene had to be selected in order to calculate baseline values.'}]

    # non-s1 is_valid_reference raise an error, while we try to find a valid s1 reference
    # do we want this behaviour for pre-calc stacks?
    if not reference.is_valid_reference():
        reference = find_new_reference(stack)
        if reference == None:
            raise ValueError('No valid state vectors on any scenes in stack, this is fatal')

    return reference, stack, warnings

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
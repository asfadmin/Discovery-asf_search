from asf_search import ASFProduct, ASFStackableProduct, ASFSearchResults
from typing import Tuple, List, Union
import pytz
from .calc import calculate_perpendicular_baselines

try:
    from ciso8601 import parse_datetime
except ImportError:
    from dateutil.parser import parse as parse_datetime

def get_baseline_from_stack(
    reference: ASFProduct, stack: ASFSearchResults
) -> Tuple[ASFSearchResults, List[dict]]:
    warnings = []

    if len(stack) == 0:
        raise ValueError("No products found matching stack parameters")

    stack = [
        product
        for product in stack
        if not product.properties["processingLevel"].lower().startswith("metadata") and
        product.baseline is not None
    ]
    reference, stack, reference_warnings = check_reference(reference, stack)

    if reference_warnings is not None:
        warnings.append(reference_warnings)

    stack = calculate_temporal_baselines(reference, stack)

    if reference.baseline_type == ASFStackableProduct.BaselineCalcType.PRE_CALCULATED:
        stack = offset_perpendicular_baselines(reference, stack)
    else:
        stack = calculate_perpendicular_baselines(
            reference.properties["sceneName"], stack
        )

        missing_state_vectors = _count_missing_state_vectors(stack)
        if missing_state_vectors > 0:
            warnings.append(
                {
                    "MISSING STATE VECTORS":
                    f'{missing_state_vectors} scenes in stack missing State Vectors, '
                    'perpendicular baseline not calculated for these scenes'
                }
            )

    return ASFSearchResults(stack), warnings


def _count_missing_state_vectors(stack) -> int:
    return len([scene for scene in stack if scene.baseline.get("noStateVectors")])


def find_new_reference(stack: ASFSearchResults) -> Union[ASFProduct, None]:
    for product in stack:
        if product.is_valid_reference():
            return product
    return None


def check_reference(reference: ASFProduct, stack: ASFSearchResults):
    warnings = None
    if reference.properties["sceneName"] not in [
        product.properties["sceneName"] for product in stack
    ]:  # Somehow the reference we built the stack from is missing?! Just pick one
        reference = stack[0]
        warnings = [
            {
                'NEW_REFERENCE':
                'A new reference scene had to be selected in order to calculate baseline values.'
            }
        ]

    # non-s1 is_valid_reference raise an error, while we try to find a valid s1 reference
    # do we want this behaviour for pre-calc stacks?
    if not reference.is_valid_reference():
        reference = find_new_reference(stack)
        if reference is None:
            raise ValueError(
                "No valid state vectors on any scenes in stack, this is fatal"
            )

    return reference, stack, warnings


def calculate_temporal_baselines(reference: ASFProduct, stack: ASFSearchResults):
    """
    Calculates temporal baselines for a stack of products based on a reference scene
    and injects those values into the stack.

    :param reference: The reference product from which to calculate temporal baselines.
    :param stack: The stack to operate on.
    :return: None, as the operation occurs in-place on the stack provided.
    """
    reference_time = parse_datetime(reference.properties["startTime"])
    if reference_time.tzinfo is None:
        reference_time = pytz.utc.localize(reference_time)

    for secondary in stack:
        secondary_time = parse_datetime(secondary.properties["startTime"])
        if secondary_time.tzinfo is None:
            secondary_time = pytz.utc.localize(secondary_time)
        secondary.properties["temporalBaseline"] = (
            secondary_time.date() - reference_time.date()
        ).days

    return stack


def offset_perpendicular_baselines(reference: ASFProduct, stack: ASFSearchResults):
    reference_offset = float(reference.baseline["insarBaseline"])

    for product in stack:
        product.properties["perpendicularBaseline"] = round(
            float(product.baseline["insarBaseline"]) - reference_offset
        )

    return stack

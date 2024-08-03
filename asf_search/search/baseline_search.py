from typing import Type
from asf_search.baseline.stack import get_baseline_from_stack
from asf_search import ASF_LOGGER
from copy import copy

from asf_search.search import search, product_search
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search import ASFProduct
from asf_search.constants import PLATFORM
from asf_search.exceptions import ASFSearchError


precalc_platforms = [
    PLATFORM.ALOS,
    PLATFORM.RADARSAT,
    PLATFORM.ERS1,
    PLATFORM.ERS2,
    PLATFORM.JERS,
]


def stack_from_product(
    reference: ASFProduct,
    opts: ASFSearchOptions = None,
    ASFProductSubclass: Type[ASFProduct] = None,
) -> ASFSearchResults:
    """
    Finds a baseline stack from a reference ASFProduct

    Parameters
    ----------
    reference:
        Reference scene to base the stack on,
        and from which to calculate perpendicular/temporal baselines
    opts:
        An ASFSearchOptions object describing the search parameters to be used.
        Search parameters specified outside this object will override in event of a conflict.
    ASFProductSubclass:
        An ASFProduct subclass constructor.

    Returns
    -------
    `asf_search.ASFSearchResults`
        list of search results of subclass ASFProduct or of provided ASFProductSubclass
    """

    opts = ASFSearchOptions() if opts is None else copy(opts)

    opts.merge_args(**dict(reference.get_stack_opts()))

    stack = search(opts=opts)

    is_complete = stack.searchComplete

    if ASFProductSubclass is not None:
        _cast_results_to_subclass(stack, ASFProductSubclass)

    stack, warnings = get_baseline_from_stack(reference=reference, stack=stack)
    stack.searchComplete = is_complete  # preserve final outcome of earlier search()

    stack.sort(key=lambda product: product.properties['temporalBaseline'])

    for warning in warnings:
        ASF_LOGGER.warning(f'{warning}')

    return stack


def stack_from_id(
    reference_id: str,
    opts: ASFSearchOptions = None,
    useSubclass: Type[ASFProduct] = None,
) -> ASFSearchResults:
    """
    Finds a baseline stack from a reference product ID

    Parameters
    ----------
    reference_id:
        Reference product to base the stack from,
        and from which to calculate perpendicular/temporal baselines
    opts:
        An ASFSearchOptions object describing the search parameters to be used.
        Search parameters specified outside this object will override in event of a conflict.
    ASFProductSubclass:
        An ASFProduct subclass constructor.

    Returns
    -------
    `asf_search.ASFSearchResults`
        list of search results of subclass ASFProduct or of provided ASFProductSubclass
    """

    opts = ASFSearchOptions() if opts is None else copy(opts)

    reference_results = product_search(product_list=reference_id, opts=opts)

    reference_results.raise_if_incomplete()

    if len(reference_results) <= 0:
        raise ASFSearchError(f'Reference product not found: {reference_id}')
    reference = reference_results[0]

    if useSubclass is not None:
        reference = _cast_to_subclass(reference, useSubclass)

    return reference.stack(opts=opts, useSubclass=useSubclass)


def _cast_results_to_subclass(stack: ASFSearchResults, ASFProductSubclass: Type[ASFProduct]):
    """
    Converts results from default ASFProduct subclasses to custom ones
    """
    for idx, product in enumerate(stack):
        stack[idx] = _cast_to_subclass(product, ASFProductSubclass)


def _cast_to_subclass(product: ASFProduct, subclass: Type[ASFProduct]) -> ASFProduct:
    """
    Casts this ASFProduct object as a new object of return type subclass.

    example:
    ```
    class MyCustomClass(ASFProduct):
        _base_properties = {
        **ASFProduct._base_properties,
        'some_unique_property': {'path': ['AdditionalAttributes', 'UNIQUE_PROPERTY', ...]}
        }

    # subclass as constructor
    customReference = reference.cast_to_subclass(MyCustomClass)
    print(customReference.properties['some_unique_property'])
    ```

    :param subclass: The ASFProduct subclass constructor to call on the product
    :returns return product as `ASFProduct` subclass
    """

    try:
        if isinstance(subclass, type(ASFProduct)):
            return subclass(
                args={'umm': product.umm, 'meta': product.meta}, session=product.session
            )
    except Exception as e:
        raise ValueError(f'Unable to use provided subclass {type(subclass)}, \nError Message: {e}')

    raise ValueError(f'Expected ASFProduct subclass constructor, got {type(subclass)}')

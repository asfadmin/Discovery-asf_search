from typing import Callable, Type, Union
from asf_search.baseline.stack import get_baseline_from_stack
from copy import copy

from asf_search.search import search, product_search
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search import ASFProduct
from asf_search.constants import PLATFORM
from asf_search.exceptions import ASFSearchError
from copy import copy

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
        ASFProductSubclass: Union[Type[ASFProduct], Callable[[ASFProduct], ASFProduct]] = None
    ) -> ASFSearchResults:
    """
    Finds a baseline stack from a reference ASFProduct

    :param reference: Reference scene to base the stack on, and from which to calculate perpendicular/temporal baselines
    :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.
    :param ASFProductSubclass: An ASFProduct subclass constructor, or a callable that takes an ASFProduct object and returns and object of type ASFProduct. 
    
    :return: ASFSearchResults(dict) of search results
    """

    opts = (ASFSearchOptions() if opts is None else copy(opts))

    opts.merge_args(**dict(reference.get_stack_opts()))

    stack = search(opts=opts)
    if ASFProductSubclass is not None:
        stack.cast_to_subclass(ASFProductSubclass)

    is_complete = stack.searchComplete

    stack, warnings = get_baseline_from_stack(reference=reference, stack=stack)
    stack.searchComplete = is_complete # preserve final outcome of earlier search()

    stack.sort(key=lambda product: product.properties['temporalBaseline'])

    return stack


def stack_from_id(
        reference_id: str,
        opts: ASFSearchOptions = None,
        ASFProductSubclass: Union[Type[ASFProduct], Callable[[ASFProduct], ASFProduct]] = None
) -> ASFSearchResults:
    """
    Finds a baseline stack from a reference product ID

    :param reference_id: Reference product to base the stack from, and from which to calculate perpendicular/temporal baselines
    :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.
    :param ASFProductSubclass: An ASFProduct subclass constructor, or a callable that takes an ASFProduct object and returns and object of type ASFProduct. 
    
    :return: ASFSearchResults(list) of search results
    """

    opts = (ASFSearchOptions() if opts is None else copy(opts))


    reference_results = product_search(product_list=reference_id, opts=opts)
    
    reference_results.raise_if_incomplete()
    
    if len(reference_results) <= 0:
        raise ASFSearchError(f'Reference product not found: {reference_id}')
    reference = reference_results[0]
    
    if ASFProductSubclass is not None:
        reference = reference.cast_to_subclass(ASFProductSubclass)
        

    return stack_from_product(reference, opts=opts, ASFProductSubclass=ASFProductSubclass)

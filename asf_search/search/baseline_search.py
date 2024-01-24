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

def stack_from_id(
        reference_id: str,
        opts: ASFSearchOptions = None,
        useSubclass: Type[ASFProduct] = None
) -> ASFSearchResults:
    """
    Finds a baseline stack from a reference product ID

    :param reference_id: Reference product to base the stack from, and from which to calculate perpendicular/temporal baselines
    :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.
    :param ASFProductSubclass: An ASFProduct subclass constructor.
    
    :return: ASFSearchResults(list) of search results
    """

    opts = (ASFSearchOptions() if opts is None else copy(opts))


    reference_results = product_search(product_list=reference_id, opts=opts)
    
    reference_results.raise_if_incomplete()
    
    if len(reference_results) <= 0:
        raise ASFSearchError(f'Reference product not found: {reference_id}')
    reference = reference_results[0]
    
    if useSubclass is not None:
        reference = ASFProduct.cast_to_subclass(reference, useSubclass)
        
    return reference.stack(opts=opts, useSubclass=useSubclass)

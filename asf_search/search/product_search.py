from typing import Sequence
from copy import copy

from asf_search.search import search
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.ASFSearchResults import ASFSearchResults


def product_search(product_list: Sequence[str], opts: ASFSearchOptions = None) -> ASFSearchResults:
    """
    Performs a product ID search using the ASF SearchAPI

    Parameters
    ----------
    :param product_list:
        List of specific products.
        Guaranteed to be at most one product per product name.
    opts:
        An ASFSearchOptions object describing the search parameters to be used.
        Search parameters specified outside this object will override in event of a conflict.

    Returns
    -------
    `asf_search.ASFSearchResults` (list of search results of subclass ASFProduct)
    """

    opts = ASFSearchOptions() if opts is None else copy(opts)

    opts.merge_args(product_list=product_list)

    return search(opts=opts)

from typing import Sequence
from copy import copy

from asf_search.search import search
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.ASFSearchResults import ASFSearchResults


def granule_search(granule_list: Sequence[str], opts: ASFSearchOptions = None) -> ASFSearchResults:
    """
    Performs a granule name search using the ASF SearchAPI

    Parameters
    ----------
    granule_list:
        List of specific granules.
        Search results may include several products per granule name.
    opts:
        An ASFSearchOptions object describing the search parameters to be used.
        Search parameters specified outside this object will override in event of a conflict.

    Returns
    -------
    `asf_search.ASFSearchResults` (list of search results of subclass ASFProduct)
    """

    opts = ASFSearchOptions() if opts is None else copy(opts)

    opts.merge_args(granule_list=granule_list)

    return search(opts=opts)

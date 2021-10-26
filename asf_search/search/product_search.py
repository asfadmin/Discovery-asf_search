from typing import Iterable
from copy import copy

from asf_search.search import search
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.ASFSession import ASFSession


def product_search(
        product_list: Iterable[str],
        cmr_provider: str = None,
        session: ASFSession = None,
        opts: ASFSearchOptions = None,
        host: str = None
) -> ASFSearchResults:
    """
    Performs a product ID search using the ASF SearchAPI

    :param product_list: List of specific products. Results guaranteed to be at most one product per product name.
    :param cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider
    :param session: A Session to be used when performing the search. For most uses, can be ignored. Used when searching for a dataset, provider, etc. that requires authentication. See also: asf_search.ASFSession
    :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes and can generally be ignored.

    :return: ASFSearchResults(list) of search results
    """

    kwargs = locals()
    data = dict((k, v) for k, v in kwargs.items() if k not in ['host', 'opts'] and v is not None)

    opts = (ASFSearchOptions() if opts is None else copy(opts))
    for p in data:
        setattr(opts, p, data[p])

    return search(opts=opts, host=host)

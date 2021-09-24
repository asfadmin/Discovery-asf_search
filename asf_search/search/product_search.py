from typing import Iterable

from asf_search.search import search
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.ASFSession import ASFSession
from asf_search.constants import INTERNAL


def product_search(
        product_list: Iterable[str],
        host: str = INTERNAL.SEARCH_API_HOST,
        asf_session: ASFSession = None,
        cmr_provider: str = None
) -> ASFSearchResults:
    """
    Performs a product ID search using the ASF SearchAPI

    :param product_list: List of specific products. Results guaranteed to be at most one product per product name.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :param cmr_token: EDL Auth Token for authenticated searches, see https://urs.earthdata.nasa.gov/user_tokens
    :param cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider

    :return: ASFSearchResults(list) of search results
    """
    kwargs = locals()
    data = dict((k,v) for k,v in kwargs.items() if k != "host" and v is not None)
    data = ASFSearchOptions(**data)

    return search(data, host=host)

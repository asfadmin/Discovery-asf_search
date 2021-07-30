from typing import Iterable

from asf_search.search import search
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.constants import INTERNAL


def granule_search(
        granule_list: Iterable[str],
        host: str = INTERNAL.SEARCH_API_HOST,
        cmr_token: str = None,
        cmr_provider: str = None
) -> ASFSearchResults:
    """
    Performs a granule name search using the ASF SearchAPI

    :param granule_list: List of specific granules. Results may include several products per granule name.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :param cmr_token: EDL Auth Token for authenticated searches, see https://urs.earthdata.nasa.gov/user_tokens
    :param cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider

    :return: ASFSearchResults(list) of search results
    """
    kwargs = locals()
    data = dict((k,v) for k,v in kwargs.items() if v is not None and v != '')

    return search(**data)

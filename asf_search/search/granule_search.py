from typing import Iterable

from asf_search.search import search
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.constants import INTERNAL


def granule_search(
        data: ASFSearchOptions,
        host: str = INTERNAL.SEARCH_API_HOST,
        cmr_token: str = None,
        cmr_provider: str = None
) -> ASFSearchResults:
    """
    Performs a granule name search using the ASF SearchAPI

    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :param cmr_token: EDL Auth Token for authenticated searches, see https://urs.earthdata.nasa.gov/user_tokens
    :param cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider

    :return: ASFSearchResults(list) of search results
    """
    # Run it through ASFSearchOptions first, for good error output:
    data = ASFSearchOptions(data)

    used_keywords = [
        "granule_list",
    ]

    # Make a new one, with ONLY the keys geo_search needs:
    data = ASFSearchOptions({ k: data[k] for k in data if k in used_keywords })

    return search(data, cmr_token=cmr_token, cmr_provider=cmr_provider)

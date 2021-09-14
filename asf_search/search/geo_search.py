from typing import Union, Iterable
import datetime

from asf_search.search import search
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.constants import INTERNAL


def geo_search(data: ASFSearchOptions, 
        host: str = INTERNAL.SEARCH_API_HOST, cmr_token: str = None, cmr_provider: str = None
        ) -> ASFSearchResults:
    """
    Performs a geographic search using the ASF SearchAPI

    :return: ASFSearchResults(list) of search results
    """
    # Run it through ASFSearchOptions first, for good error output:
    data = ASFSearchOptions(data)

    used_keywords = [
        "absoluteOrbit",
        "asfFrame",
        "beamMode",
        "collectionName",
        "end",
        "flightDirection",
        "frame",
        "instrument",
        "intersectsWith",
        "lookDirection",
        "platform",
        "polarization",
        "processingDate",
        "processingLevel",
        "relativeOrbit",
        "start",
        "maxResults",
    ]

    # Make a new one, with ONLY the keys geo_search needs:
    data = ASFSearchOptions({ k: data[k] for k in data if k in used_keywords })

    return search(data, host=host, cmr_token=cmr_token, cmr_provider=cmr_provider)

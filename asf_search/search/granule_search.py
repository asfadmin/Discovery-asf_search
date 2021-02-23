from typing import Union, Iterable
import asf_search.search

def granule_search(
        granule_list: Iterable[str],
        host: str = asf_search.INTERNAL.HOST
) -> dict:
    """
    Performs a granule name search using the ASF SearchAPI

    :param granule_list: List of specific granules. Results may include several products per granule name.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.

    :return: Dictionary of search results. Always includes 'results', may also include 'errors' and/or 'warnings'
    """

    return asf_search.search(granule_list=granule_list, host=host)

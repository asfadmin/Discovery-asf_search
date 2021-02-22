from typing import Union, Iterable
import asf_search.search

def granule_search(
        granule_list: Union[str, Iterable[str]] = None,
        host: str = None
) -> dict:
    """
    Performs a granule name search using the public ASF Search API

    :param granule_list: List of specific granules. Search results may include several products per granule name.
    :param host: REST SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :return: Dictionary of search results. Always includes 'results', may also include 'errors' and/or 'warnings'
    """
    if host is None:
        host = asf_search.INTERNAL.HOST

    if isinstance(granule_list, list):
        granule_list = ','.join(granule_list)

    data = {
        'granule_list': granule_list,
        'host': host
    }
    return asf_search.search(**data)
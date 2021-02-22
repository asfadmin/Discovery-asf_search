from typing import Union, Iterable
import asf_search.search

def granule_search(
        granule_list: Union[str, Iterable[str]] = None
) -> dict:
    """
    Performs a granule name search using the public ASF Search API

    :param granule_list: List of specific granules. Search results may include several products per granule name.
    :return: Dictionary of search results. Always includes 'results', may also include 'errors' and/or 'warnings'
    """
    if isinstance(granule_list, list):
        granule_list = ','.join(granule_list)

    data = {
        'granule_list': granule_list
    }
    return asf_search.search(**data)
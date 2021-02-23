from typing import Union, Iterable
import asf_search.search

def granule_search(
        granule_list: Iterable[str],
        host: str = asf_search.INTERNAL.HOST,
        output: str = 'geojson'
) -> dict:
    """
    Performs a granule name search using the ASF SearchAPI

    :param granule_list: List of specific granules. Results may include several products per granule name.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :param output: SearchAPI output format, can be used to alter what metadata is returned and the structure of the results.

    :return: Dictionary of search results
    """

    return asf_search.search(granule_list=granule_list, host=host, output=output)

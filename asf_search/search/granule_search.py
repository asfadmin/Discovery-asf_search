from typing import Union, Iterable
import asf_search.search


def granule_search(
        granule_list: Iterable[str],
        host: str = asf_search.INTERNAL.HOST,
        output: str = 'geojson',
        cmr_token: str = None,
        cmr_provider: str = None
) -> dict:
    """
    Performs a granule name search using the ASF SearchAPI

    :param granule_list: List of specific granules. Results may include several products per granule name.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :param output: SearchAPI output format, can be used to alter what metadata is returned and the structure of the results.
    :param cmr_token: EDL Auth Token for authenticated searches, see https://urs.earthdata.nasa.gov/user_tokens
    :param cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider

    :return: Dictionary of search results
    """
    kwargs = locals()
    data = dict((k,v) for k,v in kwargs.items() if v is not None and v != '')

    return asf_search.search(**data)

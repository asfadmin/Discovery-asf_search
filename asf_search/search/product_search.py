from typing import Union, Iterable
import asf_search.search

def product_search(
        product_list: Iterable[str],
        host: str = asf_search.INTERNAL.HOST,
        output: str = 'geojson'
) -> dict:
    """
    Performs a product ID search using the ASF SearchAPI

    :param product_list: List of specific products. Results guaranteed to be at most one product per product name.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :param output: SearchAPI output format, can be used to alter what metadata is returned and the structure of the results.

    :return: Dictionary of search results
    """

    return asf_search.search(product_list=product_list, host=host, output=output)

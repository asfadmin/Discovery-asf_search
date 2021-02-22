from typing import Union, Iterable
import asf_search.search

def product_search(
        product_list: Union[str, Iterable[str]] = None,
        host: str = None
) -> dict:
    """
    Performs a product ID search using the ASF SearchAPI

    :param product_list: List of specific products. Guaranteed to be at most one product per product name.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :return: Dictionary of search results. Always includes 'results', may also include 'errors' and/or 'warnings'
    """
    if host is None:
        host = asf_search.INTERNAL.HOST

    if isinstance(product_list, list):
        product_list = ','.join(product_list)

    data = {
        'product_list': product_list,
        'host': host
    }
    return asf_search.search(**data)
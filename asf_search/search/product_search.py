from typing import Union, Iterable
import asf_search.search

def product_search(
        product_list: Union[str, Iterable[str]] = None
) -> dict:
    """
    Performs a product ID search using the public ASF Search API

    :param product_list: List of specific products. Guaranteed to be at most one product per product name.
    :return: Dictionary of search results. Always includes 'results', may also include 'errors' and/or 'warnings'
    """
    if isinstance(product_list, list):
        product_list = ','.join(product_list)

    data = {
        'product_list': product_list
    }
    return asf_search.search(**data)
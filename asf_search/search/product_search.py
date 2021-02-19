from typing import Union
import asf_search.search

def product_search(
        product_list: Union[list, str] = None
) -> dict:
    if isinstance(product_list, list):
        product_list = ','.join(product_list)

    data = {
        'product_list': product_list
    }
    return asf_search.search(**data)
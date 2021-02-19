from typing import Union
import asf_search.search

def granule_search(
        granule_list: Union[list, str] = None
) -> dict:
    if isinstance(granule_list, list):
        granule_list = ','.join(granule_list)

    data = {
        'granule_list': granule_list
    }
    return asf_search.search(**data)
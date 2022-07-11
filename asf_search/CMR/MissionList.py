from typing import Dict, List
from asf_search.exceptions import CMRError
from asf_search.constants.INTERNAL import CMR_HOST, CMR_COLLECTIONS_PATH

import requests


def get_campaigns(data) -> Dict:
    """Queries CMR Collections endpoint for 
    collections associated with the given platform

    :param data: a dictionary with required keys:
    'include_facets', 'provider', 'platform[]' and optional key: 'instrument[]'

    :return: Dictionary containing CMR umm_json response
    """
    response = requests.post('https://' + CMR_HOST + CMR_COLLECTIONS_PATH,
                             data=data)
    if response.status_code != 200:
        raise CMRError(f'CMR_ERROR {response.status_code}: {response.text}')

    try:
        data = response.json()
    except Exception as e:
        raise CMRError(f'CMR_ERROR: Error parsing JSON from CMR: {e}')

    return data

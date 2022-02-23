from typing import List
from asf_search.exceptions import CMRError
from asf_search.constants.INTERNAL import CMR_HOST, CMR_COLLECTIONS

import requests


def get_collections(data) -> List[str]:
    response = requests.post('https://' + CMR_HOST + CMR_COLLECTIONS,
                      data=data)
    if response.status_code != 200:
        raise CMRError(f'CMR_ERROR {response.status_code}: {response.text}')

    try:
        data = response.json()
    except Exception as e:
        raise CMRError(f'CMR_ERROR: Error parsing JSON from CMR: {e}')

    return data

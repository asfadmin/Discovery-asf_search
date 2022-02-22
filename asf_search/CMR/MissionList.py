from typing import List
from asf_search.exceptions import CMRError
from asf_search.constants.INTERNAL import CMR_HOST, CMR_COLLECTIONS
from defusedxml.lxml import fromstring

import requests


def getMissions(data) -> List[str]:
    response = requests.post('https://' + CMR_HOST + CMR_COLLECTIONS,
                      data=data)
    if response.status_code != 200:
        raise CMRError(f'CMR_ERROR {response.status_code}: {response.text}')

    try:
        root = fromstring(response.text.encode('latin-1'))
    except Exception as e:
        raise CMRError(f'CMR_ERROR: Error parsing XML from CMR: {e}')

    missions = [f.text for f in root.findall('.//facets/facet[@field="project"]/value')]
    missions = sorted(missions, key=lambda s: s.casefold())

    return missions

import requests
import datetime
import json
from typing import Union
import asf_search.constants

def search(
        absoluteorbit: Union[list, int, range] = None,
        asfframe: Union[list, int, range] = None,
        beammode: Union[list, str] = None,
        collectionname: Union[list, str] = None,
        dataset: Union[list, str] = None,
        end: datetime = None,
        flightdirection: Union[list, str] = None,
        frame: Union[list, int, range] = None,
        granule_list: Union[list, str] = None,
        groupid: Union[list, str] = None,
        instrument: Union[list, str] = None,
        intersectswith: str = None,
        lookdirection: Union[list, str] = None,
        maxresults: int = None,
        platform: Union[list, str] = None,
        polarization: Union[list, str] = None,
        processingdate: datetime = None,
        processinglevel: Union[list, str] = None,
        product_list: Union[list, str] = None,
        relativeorbit: Union[list, int, range] = None,
        start: datetime = None
) -> dict:
    kwargs = locals()
    data = dict((k,v) for k,v in kwargs.items() if v is not None and v != '')
    data['output'] = 'jsonlite'
    response = requests.post(f'https://{asf_search.INTERNAL.HOST}{asf_search.INTERNAL.SEARCH_PATH}', data=data)
    return json.loads(requests.post(f'https://{asf_search.INTERNAL.HOST}{asf_search.INTERNAL.SEARCH_PATH}', data=data).text)
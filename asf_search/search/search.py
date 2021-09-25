from typing import Union, Iterable, Tuple
import requests
from requests.exceptions import HTTPError
import datetime
import math

from asf_search import __version__
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.ASFSession import ASFSession
from asf_search.ASFProduct import ASFProduct
from asf_search.exceptions import ASFSearch4xxError, ASFSearch5xxError, ASFServerError
from asf_search.constants import INTERNAL


def search(data: ASFSearchOptions, 
        host: str = INTERNAL.SEARCH_API_HOST,
        ) -> ASFSearchResults:
    """
    Performs a generic search using the ASF SearchAPI

    :return: ASFSearchResults(list) of search results
    """
    # Make sure data is a ASFSearchOptions 'dict', to get the params verified:
    if type(data) is not ASFSearchOptions:
        data = ASFSearchOptions(**data)
    # Set some defaults:
    if data.cmr_provider is None:
        data.cmr_provider = "ASF"
    if data.asf_session is None:
        data.asf_session = ASFSession()

    listify_fields = [
        'absoluteOrbit',
        'asfFrame',
        'beamMode',
        'collectionName',
        'frame',
        'granule_list',
        'groupID',
        'instrument',
        'lookDirection',
        'offNadirAngle',
        'platform',
        'polarization',
        'processingLevel',
        'product_list',
        'relativeOrbit'
    ]
    for key in listify_fields:
        if key in data and not isinstance(data[key], list):
            data[key] = [data[key]]

    flatten_fields = [
        'absoluteOrbit',
        'asfFrame',
        'frame',
        'offNadirAngle',
        'relativeOrbit']
    for key in flatten_fields:
        if key in data:
            data[key] = flatten_list(data[key])

    join_fields = [
        'beamMode',
        'collectionName',
        'flightDirection',
        'granule_list',
        'groupID',
        'instrument',
        'lookDirection',
        'platform',
        'polarization',
        'processingLevel',
        'product_list']
    for key in join_fields:
        if key in data:
            data[key] = ','.join(data[key])

    data = dict(data)
    data['output'] = 'geojson'

    response = data["asf_session"].post(f'https://{host}{INTERNAL.SEARCH_PATH}', data=data)

    try:
        response.raise_for_status()
    except HTTPError:
        if 400 <= response.status_code <= 499:
            raise ASFSearch4xxError(f'HTTP {response.status_code}: {response.json()["error"]["report"]}')
        if 500 <= response.status_code <= 599:
            raise ASFSearch5xxError(f'HTTP {response.status_code}: {response.json()["error"]["report"]}')
        raise ASFServerError(f'HTTP {response.status_code}: {response.json()["error"]["report"]}')

    products = [ASFProduct(f) for f in response.json()['features']]
    return ASFSearchResults(products)


def flatten_list(items: Iterable[Union[float, Tuple[float, float]]]) -> str:
    """
    Converts a list of numbers and/or min/max tuples to a string of comma-separated numbers and/or ranges.
    Example: [1,2,3,(10,20)] -> '1,2,3,10-20'

    :param items: The list of numbers and/or min/max tuples to flatten

    :return: String containing comma-separated representation of input, min/max tuples converted to 'min-max' format

    :raises ValueError: if input list contains tuples with fewer or more than 2 values, or if a min/max tuple in the input list is descending
    :raises TypeError: if input list contains non-numeric values
    """

    for item in items:
        if isinstance(item, tuple):
            if len(item) < 2:
                raise ValueError(f'Not enough values in min/max tuple: {item}')
            if len(item) > 2:
                raise ValueError(f'Too many values in min/max tuple: {item}')
            if not isinstance(item[0], (int, float, complex)) and not isinstance(item[0], bool):
                raise TypeError(f'Expected numeric min in tuple, got {type(item[0])}: {item}')
            if not isinstance(item[1], (int, float, complex)) and not isinstance(item[1], bool):
                raise TypeError(f'Expected numeric max in tuple, got {type(item[1])}: {item}')
            if math.isinf(item[0]) or math.isnan(item[0]):
                raise ValueError(f'Expected finite numeric min in min/max tuple, got {item[0]}: {item}')
            if math.isinf(item[1]) or math.isnan(item[1]):
                raise ValueError(f'Expected finite numeric max in min/max tuple, got {item[1]}: {item}')
            if item[0] > item[1]:
                raise ValueError(f'Min must be less than max when using min/max tuples to search: {item}')
        elif isinstance(item, (int, float, complex)) and not isinstance(item, bool):
            if math.isinf(item) or math.isnan(item):
                raise ValueError(f'Expected finite numeric value, got {item}')
        elif not isinstance(item, (int, float, complex)) and not isinstance(item, bool):
            raise TypeError(f'Expected number or min/max tuple, got {type(item)}')

    return ','.join([f'{item[0]}-{item[1]}' if isinstance(item, tuple) else f'{item}' for item in items])

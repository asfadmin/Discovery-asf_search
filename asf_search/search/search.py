from typing import Union, Iterable, Tuple
import requests
from requests.exceptions import HTTPError
import datetime
import math

from asf_search import __version__
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.ASFProduct import ASFProduct
from asf_search.exceptions import ASFSearch4xxError, ASFSearch5xxError, ASFServerError
from asf_search.constants import INTERNAL


def search(
        absoluteOrbit: Union[int, Tuple[int, int], Iterable[Union[int, Tuple[int, int]]]] = None,
        asfFrame: Union[int, Tuple[int, int], Iterable[Union[int, Tuple[int, int]]]] = None,
        beamMode: Union[str, Iterable[str]] = None,
        collectionName: Union[str, Iterable[str]] = None,
        maxDoppler: float = None,
        minDoppler: float = None,
        end: Union[datetime.datetime, str] = None,
        maxFaradayRotation: float = None,
        minFaradayRotation: float = None,
        flightDirection: str = None,
        flightLine: str = None,
        frame: Union[int, Tuple[int, int], Iterable[Union[int, Tuple[int, int]]]] = None,
        granule_list: Union[str, Iterable[str]] = None,
        groupID: Union[str, Iterable[str]] = None,
        insarStackId: str = None,
        instrument: Union[str, Iterable[str]] = None,
        intersectsWith: str = None,
        lookDirection: Union[str, Iterable[str]] = None,
        offNadirAngle: Union[float, Tuple[float, float], Iterable[Union[float, Tuple[float, float]]]] = None,
        platform: Union[str, Iterable[str]] = None,
        polarization: Union[str, Iterable[str]] = None,
        processingDate: Union[datetime.datetime, str] = None,
        processingLevel: Union[str, Iterable[str]] = None,
        product_list: Union[str, Iterable[str]] = None,
        relativeOrbit: Union[int, Tuple[int, int], Iterable[Union[int, Tuple[int, int]]]] = None,
        season: Tuple[int, int] = None,
        start: Union[datetime.datetime, str] = None,
        maxResults: int = None,
        host: str = INTERNAL.SEARCH_API_HOST,
        cmr_token: str = None,
        cmr_provider: str = None
) -> ASFSearchResults:
    """
    Performs a generic search using the ASF SearchAPI

    :param absoluteOrbit: For ALOS, ERS-1, ERS-2, JERS-1, and RADARSAT-1, Sentinel-1A, Sentinel-1B this value corresponds to the orbit count within the orbit cycle. For UAVSAR it is the Flight ID.
    :param asfFrame: This is primarily an ASF / JAXA frame reference. However, some platforms use other conventions. See ‘frame’ for ESA-centric frame searches.
    :param beamMode: The beam mode used to acquire the data.
    :param collectionName: For UAVSAR and AIRSAR data collections only. Search by general location, site description, or data grouping as supplied by flight agency or project.
    :param maxDoppler: Doppler provides an indication of how much the look direction deviates from the ideal perpendicular flight direction acquisition.
    :param minDoppler: Doppler provides an indication of how much the look direction deviates from the ideal perpendicular flight direction acquisition.
    :param end: End date of data acquisition. Supports timestamps as well as natural language such as "3 weeks ago"
    :param maxFaradayRotation: Rotation of the polarization plane of the radar signal impacts imagery, as HH and HV signals become mixed.
    :param minFaradayRotation: Rotation of the polarization plane of the radar signal impacts imagery, as HH and HV signals become mixed.
    :param flightDirection: Satellite orbit direction during data acquisition
    :param flightLine: Specify a flightline for UAVSAR or AIRSAR.
    :param frame: ESA-referenced frames are offered to give users a universal framing convention. Each ESA frame has a corresponding ASF frame assigned. See also: asfframe
    :param granule_list: List of specific granules. Search results may include several products per granule name.
    :param groupID: Identifier used to find products considered to be of the same scene but having different granule names
    :param insarStackId: Identifier used to find products of the same InSAR stack
    :param instrument: The instrument used to acquire the data. See also: platform
    :param intersectsWith: Search by polygon, linestring, or point defined in 2D Well-Known Text (WKT)
    :param lookDirection: Left or right look direction during data acquisition
    :param offNadirAngle: Off-nadir angles for ALOS PALSAR
    :param platform: Remote sensing platform that acquired the data. Platforms that work together, such as Sentinel-1A/1B and ERS-1/2 have multi-platform aliases available. See also: instrument
    :param polarization: A property of SAR electromagnetic waves that can be used to extract meaningful information about surface properties of the earth.
    :param processingDate: Used to find data that has been processed at ASF since a given time and date. Supports timestamps as well as natural language such as "3 weeks ago"
    :param processingLevel: Level to which the data has been processed
    :param product_list: List of specific products. Guaranteed to be at most one product per product name.
    :param relativeOrbit: Path or track of satellite during data acquisition. For UAVSAR it is the Line ID.
    :param season: Start and end day of year for desired seasonal range. This option is used in conjunction with start/end to specify a seasonal range within an overall date range.
    :param start: Start date of data acquisition. Supports timestamps as well as natural language such as "3 weeks ago"
    :param maxResults: The maximum number of results to be returned by the search
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :param cmr_token: EDL authentication token for authenticated searches, see https://urs.earthdata.nasa.gov/user_tokens
    :param cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider

    :return: ASFSearchResults(list) of search results
    """

    kwargs = locals()
    data = dict((k,v) for k,v in kwargs.items() if v is not None and v != '')
    host = data.pop('host')

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

    data['output'] = 'geojson'

    headers = {'User-Agent': f'{__name__}.{__version__}'}
    response = requests.post(f'https://{host}{INTERNAL.SEARCH_PATH}', data=data, headers=headers)

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

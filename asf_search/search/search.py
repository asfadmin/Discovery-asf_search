from typing import Union, Iterable
import requests
import datetime
import json
import asf_search


def search(
        absoluteOrbit: Iterable[Union[int, range]] = None,
        asfFrame: Iterable[Union[int, range]] = None,
        beamMode: Iterable[str] = None,
        collectionName: Iterable[str] = None,
        end: Union[datetime.datetime, str] = None,
        flightDirection: Iterable[str] = None,
        frame: Iterable[Union[int, range]] = None,
        granule_list: Iterable[str] = None,
        groupID: Iterable[str] = None,
        instrument: Iterable[str] = None,
        intersectsWith: str = None,
        lookDirection: Iterable[str] = None,
        platform: Iterable[str] = None,
        polarization: Iterable[str] = None,
        processingDate: Union[datetime.datetime, str] = None,
        processingLevel: Iterable[str] = None,
        product_list: Iterable[str] = None,
        relativeOrbit: Iterable[Union[int, range]] = None,
        start: Union[datetime.datetime, str] = None,
        maxResults: int = None,
        host: str = asf_search.INTERNAL.HOST,
        output: str = 'geojson',
        cmr_token: str = None,
        cmr_provider: str = None
) -> dict:
    """
    Performs a generic search using the ASF SearchAPI

    :param absoluteOrbit: For ALOS, ERS-1, ERS-2, JERS-1, and RADARSAT-1, Sentinel-1A, Sentinel-1B this value corresponds to the orbit count within the orbit cycle. For UAVSAR it is the Flight ID.
    :param asfFrame: This is primarily an ASF / JAXA frame reference. However, some platforms use other conventions. See ‘frame’ for ESA-centric frame searches.
    :param beamMode: The beam mode used to acquire the data.
    :param collectionName: For UAVSAR and AIRSAR data collections only. Search by general location, site description, or data grouping as supplied by flight agency or project.
    :param end: End date of data acquisition. Supports timestamps as well as natural language such as "3 weeks ago"
    :param flightDirection: Satellite orbit direction during data acquisition
    :param frame: ESA-referenced frames are offered to give users a universal framing convention. Each ESA frame has a corresponding ASF frame assigned. See also: asfframe
    :param granule_list: List of specific granules. Search results may include several products per granule name.
    :param groupID: Identifier used to find products considered to be of the same scene but having different granule names
    :param instrument: The instrument used to acquire the data. See also: platform
    :param intersectsWith: Search by polygon, linestring, or point defined in 2D Well-Known Text (WKT)
    :param lookDirection: Left or right look direction during data acquisition
    :param maxResults: The maximum number of results to be returned by the search
    :param platform: Remote sensing platform that acquired the data. Platforms that work together, such as Sentinel-1A/1B and ERS-1/2 have multi-platform aliases available. See also: instrument
    :param polarization: A property of SAR electromagnetic waves that can be used to extract meaningful information about surface properties of the earth.
    :param processingDate: Used to find data that has been processed at ASF since a given time and date. Supports timestamps as well as natural language such as "3 weeks ago"
    :param processingLevel: Level to which the data has been processed
    :param product_list: List of specific products. Guaranteed to be at most one product per product name.
    :param relativeOrbit: Path or track of satellite during data acquisition. For UAVSAR it is the Line ID.
    :param start: Start date of data acquisition. Supports timestamps as well as natural language such as "3 weeks ago"
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :param output: SearchAPI output format, can be used to alter what metadata is returned and the structure of the results.
    :param cmr_token: EDL Auth Token for authenticated searches, see https://urs.earthdata.nasa.gov/user_tokens
    :param cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider

    :return: Dictionary of search results
    """

    kwargs = locals()
    data = dict((k,v) for k,v in kwargs.items() if v is not None and v != '')
    host = data.pop('host')

    flatten_fields = [
        'absoluteOrbit',
        'asfFrame',
        'frame',
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

    headers = {'User-Agent': f'{asf_search.__name__}.{asf_search.__version__}'}

    response = requests.post(f'https://{host}{asf_search.INTERNAL.SEARCH_PATH}', data=data, headers=headers)

    if data['output'] == 'count':
        return {'count': int(response.text)}
    return json.loads(response.text)


def flatten_list(items: Iterable[Union[int, range]]) -> str:
    """
    Converts a list of ints and/or ranges to a string of comma-separated ints and/or ranges.
    Example: [1,2,3,range(4,10)] -> '1,2,3,4-10'

    :param items: The list of ints and/or ranges to flatten

    :return: String containing comma-separated representation of input, ranges converted to 'start-stop' format

    :raises ValueError: if input list contains non-int and non-range values, or if a range in the input list has a Step
    != 1, or if a range in the input list is descending
    """

    for item in items:
        if isinstance(item, range):
            if item.step != 1:
                raise ValueError(f'Step must be 1 when using ranges to search: {item}')
            if item.start > item.stop:
                raise ValueError(f'Start must be less than Stop when using ranges to search: {item}')
        elif not isinstance(item, int):
            raise ValueError(f'Expected int or range, got {type(item)}')

    return ','.join([f'{item.start}-{item.stop}' if isinstance(item, range) else f'{item}' for item in items])

import requests
import datetime
import json
from typing import Union, Iterable
import asf_search.constants

def search(
        absoluteorbit: Iterable[Union[int, range]] = None,
        asfframe: Iterable[Union[int, range]] = None,
        beammode: Iterable[str] = None,
        collectionname: Iterable[str] = None,
        end: datetime = None,
        flightdirection: Iterable[str] = None,
        frame: Iterable[Union[int, range]] = None,
        granule_list: Iterable[str] = None,
        groupid: Iterable[str] = None,
        instrument: Iterable[str] = None,
        intersectswith: str = None,
        lookdirection: Iterable[str] = None,
        maxresults: int = None,
        platform: Iterable[str] = None,
        polarization: Iterable[str] = None,
        processingdate: datetime = None,
        processinglevel: Iterable[str] = None,
        product_list: Iterable[str] = None,
        relativeorbit: Iterable[Union[int, range]] = None,
        start: datetime = None,
        host: str = None
) -> dict:
    """
    Performs a generic search using the ASF SearchAPI

    :param absoluteorbit: For ALOS, ERS-1, ERS-2, JERS-1, and RADARSAT-1, Sentinel-1A, Sentinel-1B this value corresponds to the orbit count within the orbit cycle. For UAVSAR it is the Flight ID.
    :param asfframe: This is primarily an ASF / JAXA frame reference. However, some platforms use other conventions. See ‘frame’ for ESA-centric frame searches.
    :param beammode: The beam mode used to acquire the data.
    :param collectionname: For UAVSAR and AIRSAR data collections only. Search by general location, site description, or data grouping as supplied by flight agency or project.
    :param end: End date of data acquisition. Supports timestamps as well as natural language such as "3 weeks ago"
    :param flightdirection: Satellite orbit direction during data acquisition
    :param frame: ESA-referenced frames are offered to give users a universal framing convention. Each ESA frame has a corresponding ASF frame assigned. See also: asfframe
    :param granule_list: List of specific granules. Search results may include several products per granule name.
    :param groupid: Identifier used to find products considered to be of the same scene but having different granule names
    :param instrument: The instrument used to acquire the data. See also: platform
    :param intersectswith: Search by polygon, linestring, or point defined in 2D Well-Known Text (WKT)
    :param lookdirection: Left or right look direction during data acquisition
    :param maxresults: The maximum number of results to be returned by the search
    :param platform: Remote sensing platform that acquired the data. Platforms that work together, such as Sentinel-1A/1B and ERS-1/2 have multi-platform aliases available. See also: instrument
    :param polarization: A property of SAR electromagnetic waves that can be used to extract meaningful information about surface properties of the earth.
    :param processingdate: Used to find data that has been processed at ASF since a given time and date
    :param processinglevel: Level to which the data has been processed
    :param product_list: List of specific products. Guaranteed to be at most one product per product name.
    :param relativeorbit: Path or track of satellite during data acquisition. For UAVSAR it is the Line ID.
    :param start: Start date of data acquisition. Supports timestamps as well as natural language such as "3 weeks ago"
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.

    :return: Dictionary of search results. Always includes 'results', may also include 'errors' and/or 'warnings'
    """

    kwargs = locals()
    data = dict((k,v) for k,v in kwargs.items() if v is not None and v != '')
    host = data.pop('host', asf_search.INTERNAL.HOST)

    data['output'] = 'geojson'
    response = requests.post(f'https://{host}{asf_search.INTERNAL.SEARCH_PATH}', data=data)
    return json.loads(response.text)
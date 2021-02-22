import requests
import datetime
import json
from typing import Union, Iterable
import asf_search.constants

def search(
        absoluteorbit: Union[int, range, Iterable[Union[int, range]]] = None,
        asfframe: Union[int, range, Iterable[Union[int, range]]] = None,
        beammode: Union[str, Iterable[str]] = None,
        collectionname: Union[str, Iterable[str]] = None,
        dataset: Union[str, Iterable[str]] = None,
        end: datetime = None,
        flightdirection: Union[str, Iterable[str]] = None,
        frame: Union[int, range, Iterable[Union[int, range]]] = None,
        granule_list: Union[str, Iterable[str]] = None,
        groupid: Union[str, Iterable[str]] = None,
        instrument: Union[str, Iterable[str]] = None,
        intersectswith: str = None,
        lookdirection: Union[str, Iterable[str]] = None,
        maxresults: int = None,
        platform: Union[str, Iterable[str]] = None,
        polarization: Union[str, Iterable[str]] = None,
        processingdate: datetime = None,
        processinglevel: Union[str, Iterable[str]] = None,
        product_list: Union[str, Iterable[str]] = None,
        relativeorbit: Union[int, range, Iterable[Union[int, range]]] = None,
        start: datetime = None
) -> dict:
    """
    Performs a generic search using the public ASF Search API

    :param absoluteorbit: For ALOS, ERS-1, ERS-2, JERS-1, and RADARSAT-1, Sentinel-1A, Sentinel-1B this value corresponds to the orbit count within the orbit cycle. For UAVSAR it is the Flight ID.
    :param asfframe: This is primarily an ASF / JAXA frame reference. However, some platforms use other conventions. See ‘frame’ for ESA-centric frame searches.
    :param beammode: The beam mode used to acquire the data.
    :param collectionname: For UAVSAR and AIRSAR data collections only. Search by general location, site description, or data grouping as supplied by flight agency or project.
    :param dataset: A shorthand identifier for a platform, instrument pair. See also: platform, instrument
    :param end: End date of data acquisition. Supports timestamps as well as natural language such as "3 weeks ago"
    :param flightdirection: Satellite orbit direction during data acquisition
    :param frame: ESA-referenced frames are offered to give users a universal framing convention. Each ESA frame has a corresponding ASF frame assigned. See also: asfframe
    :param granule_list: List of specific granules. Search results may include several products per granule name.
    :param groupid: Identifier used to find products considered to be of the same scene but having different granule names
    :param instrument: The instrument used to acquire the data. See also: platform, dataset
    :param intersectswith: Search by polygon, linestring, or point defined in 2D Well-Known Text (WKT)
    :param lookdirection: Left or right direction of data acquisition
    :param maxresults: The maximum number of results to be returned by the search
    :param platform: Remote sensing platform that acquired the data. Datasets that work together, such as Sentinel-1A/1B and ERS-1/2 have multi-platform aliases available. See also: dataset, instrument
    :param polarization: A property of SAR electromagnetic waves that can be used to extract meaningful information about surface properties of the earth.
    :param processingdate: Used to find data that has been processed at ASF since a given time and date
    :param processinglevel: Level to which the data has been processed
    :param product_list: List of specific products. Guaranteed to be at most one product per product name.
    :param relativeorbit: Path or track of satellite during data acquisition. For UAVSAR it is the Line ID.
    :param start: Start date of data acquisition. Supports timestamps as well as natural language such as "3 weeks ago"
    :return: Dictionary of search results. Always includes 'results', may also include 'errors' and/or 'warnings'
    """
    kwargs = locals()
    data = dict((k,v) for k,v in kwargs.items() if v is not None and v != '')
    data['output'] = 'jsonlite'
    response = requests.post(f'https://{asf_search.INTERNAL.HOST}{asf_search.INTERNAL.SEARCH_PATH}', data=data)
    return json.loads(requests.post(f'https://{asf_search.INTERNAL.HOST}{asf_search.INTERNAL.SEARCH_PATH}', data=data).text)
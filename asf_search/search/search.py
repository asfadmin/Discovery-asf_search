from typing import Union, Iterable, Tuple
from copy import copy
import datetime

from asf_search import ASFSearchResults
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.search.search_generator import search_generator

def search(
        absoluteOrbit: Union[int, Tuple[int, int], Iterable[Union[int, Tuple[int, int]]]] = None,
        asfFrame: Union[int, Tuple[int, int], Iterable[Union[int, Tuple[int, int]]]] = None,
        beamMode: Union[str, Iterable[str]] = None,
        beamSwath: Union[str, Iterable[str]] = None,
        campaign: Union[str, Iterable[str]] = None,
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
        absoluteBurstID: Union[int, Iterable[int]] = None,
        relativeBurstID: Union[int, Iterable[int]] = None,
        fullBurstID: Union[str, Iterable[str]] = None,
        maxResults: int = None,
        opts: ASFSearchOptions = None,
) -> ASFSearchResults:
    """
    Performs a generic search using the ASF SearchAPI. Accepts a number of search parameters, and/or an ASFSearchOptions object. If an ASFSearchOptions object is provided as well as other specific parameters, the two sets of options will be merged, preferring the specific keyword arguments.

    :param absoluteOrbit: For ALOS, ERS-1, ERS-2, JERS-1, and RADARSAT-1, Sentinel-1A, Sentinel-1B this value corresponds to the orbit count within the orbit cycle. For UAVSAR it is the Flight ID.
    :param asfFrame: This is primarily an ASF / JAXA frame reference. However, some platforms use other conventions. See ‘frame’ for ESA-centric frame searches.
    :param beamMode: The beam mode used to acquire the data.
    :param beamSwath: Encompasses a look angle and beam mode.
    :param campaign: For UAVSAR and AIRSAR data collections only. Search by general location, site description, or data grouping as supplied by flight agency or project.
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
    :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.

    :return: ASFSearchResults(list) of search results
    """
    kwargs = locals()
    data = dict((k, v) for k, v in kwargs.items() if k not in ['host', 'opts'] and v is not None)

    opts = (ASFSearchOptions() if opts is None else copy(opts))
    opts.merge_args(**data)

    results = ASFSearchResults([])
    
    # The last page will be marked as complete if results sucessful
    for page in search_generator(opts=opts):
        results.extend(page)
        results.searchComplete = page.searchComplete
        results.searchOptions = page.searchOptions
    
    results.sort(key=lambda p: (p.properties['stopTime'], p.properties['fileID']), reverse=True)
    
    return results

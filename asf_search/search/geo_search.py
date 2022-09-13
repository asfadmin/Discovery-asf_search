from typing import Union, Iterable
import datetime
from copy import copy

from asf_search.search import search
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.ASFSearchResults import ASFSearchResults


def geo_search(
        intersectsWith: str,
        absoluteOrbit: Iterable[Union[int, range]] = None,
        asfFrame: Iterable[Union[int, range]] = None,
        beamMode: Iterable[str] = None,
        beamSwath: Union[str, Iterable[str]] = None,
        campaign: Union[str, Iterable[str]] = None,
        end: Union[datetime.datetime, str] = None,
        flightDirection: Iterable[str] = None,
        frame: Iterable[Union[int, range]] = None,
        instrument: Iterable[str] = None,
        lookDirection: Iterable[str] = None,
        platform: Iterable[str] = None,
        polarization: Iterable[str] = None,
        processingDate: Union[datetime.datetime, str] = None,
        processingLevel: Iterable[str] = None,
        relativeOrbit: Iterable[Union[int, range]] = None,
        start: Union[datetime.datetime, str] = None,
        maxResults: int = None,
        opts: ASFSearchOptions = None
) -> ASFSearchResults:
    """
    Performs a geographic search using the ASF SearchAPI

    :param absoluteOrbit: For ALOS, ERS-1, ERS-2, JERS-1, and RADARSAT-1, Sentinel-1A, Sentinel-1B this value corresponds to the orbit count within the orbit cycle. For UAVSAR it is the Flight ID.
    :param asfFrame: This is primarily an ASF / JAXA frame reference. However, some platforms use other conventions. See ‘frame’ for ESA-centric frame searches.
    :param beamMode: The beam mode used to acquire the data.
    :param beamSwath: Encompasses a look angle and beam mode.
    :param campaign: For UAVSAR and AIRSAR data collections only. Search by general location, site description, or data grouping as supplied by flight agency or project.
    :param end: End date of data acquisition. Supports timestamps as well as natural language such as "3 weeks ago"
    :param flightDirection: Satellite orbit direction during data acquisition
    :param frame: ESA-referenced frames are offered to give users a universal framing convention. Each ESA frame has a corresponding ASF frame assigned. See also: asfframe
    :param instrument: The instrument used to acquire the data. See also: platform
    :param intersectsWith: Search by polygon, linestring, or point defined in 2D Well-Known Text (WKT)
    :param lookDirection: Left or right look direction during data acquisition
    :param platform: Remote sensing platform that acquired the data. Platforms that work together, such as Sentinel-1A/1B and ERS-1/2 have multi-platform aliases available. See also: instrument
    :param polarization: A property of SAR electromagnetic waves that can be used to extract meaningful information about surface properties of the earth.
    :param processingDate: Used to find data that has been processed at ASF since a given time and date.  Supports timestamps as well as natural language such as "3 weeks ago"
    :param processingLevel: Level to which the data has been processed
    :param relativeOrbit: Path or track of satellite during data acquisition. For UAVSAR it is the Line ID.
    :param start: Start date of data acquisition. Supports timestamps as well as natural language such as "3 weeks ago"
    :param maxResults: The maximum number of results to be returned by the search
    :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.

    :return: ASFSearchResults(list) of search results
    """

    kwargs = locals()
    data = dict((k, v) for k, v in kwargs.items() if k not in ['host', 'opts'] and v is not None)

    opts = (ASFSearchOptions() if opts is None else copy(opts))
    opts.merge_args(**data)

    return search(opts=opts)

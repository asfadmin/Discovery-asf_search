import time
from typing import Union, Sequence, Tuple
from copy import copy
import datetime

from asf_search import ASF_LOGGER, ASFSearchResults
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.search.search_generator import search_generator


def search(
    absoluteOrbit: Union[
        int, Tuple[int, int], range, Sequence[Union[int, Tuple[int, int], range]]
    ] = None,
    asfFrame: Union[
        int, Tuple[int, int], range, Sequence[Union[int, Tuple[int, int], range]]
    ] = None,
    beamMode: Union[str, Sequence[str]] = None,
    beamSwath: Union[str, Sequence[str]] = None,
    campaign: Union[str, Sequence[str]] = None,
    maxDoppler: float = None,
    minDoppler: float = None,
    end: Union[datetime.datetime, str] = None,
    maxFaradayRotation: float = None,
    minFaradayRotation: float = None,
    flightDirection: str = None,
    flightLine: str = None,
    frame: Union[int, Tuple[int, int], range, Sequence[Union[int, Tuple[int, int], range]]] = None,
    granule_list: Union[str, Sequence[str]] = None,
    groupID: Union[str, Sequence[str]] = None,
    insarStackId: str = None,
    instrument: Union[str, Sequence[str]] = None,
    intersectsWith: str = None,
    lookDirection: Union[str, Sequence[str]] = None,
    offNadirAngle: Union[
        float, Tuple[float, float], Sequence[Union[float, Tuple[float, float]]]
    ] = None,
    platform: Union[str, Sequence[str]] = None,
    polarization: Union[str, Sequence[str]] = None,
    processingDate: Union[datetime.datetime, str] = None,
    processingLevel: Union[str, Sequence[str]] = None,
    product_list: Union[str, Sequence[str]] = None,
    relativeOrbit: Union[
        int, Tuple[int, int], range, Sequence[Union[int, Tuple[int, int], range]]
    ] = None,
    season: Tuple[int, int] = None,
    start: Union[datetime.datetime, str] = None,
    absoluteBurstID: Union[int, Sequence[int]] = None,
    relativeBurstID: Union[int, Sequence[int]] = None,
    fullBurstID: Union[str, Sequence[str]] = None,
    collections: Union[str, Sequence[str]] = None,
    temporalBaselineDays: Union[str, Sequence[str]] = None,
    operaBurstID: Union[str, Sequence[str]] = None,
    dataset: Union[str, Sequence[str]] = None,
    shortName: Union[str, Sequence[str]] = None,
    cmr_keywords: Union[Tuple[str, str], Sequence[Tuple[str, str]]] = None,
    maxResults: int = None,
    opts: ASFSearchOptions = None,
) -> ASFSearchResults:
    """
    Performs a generic search against the Central Metadata Repository (CMR),
    returning all results in a single list.
    (For accessing results page by page see `asf_search.search_generator()`)

    Accepts a number of search parameters, and/or an ASFSearchOptions object.
    If an ASFSearchOptions object is provided as well as other specific parameters,
    the two sets of options will be merged, preferring the specific keyword arguments.

    Parameters
    ----------
    absoluteOrbit:
        For ALOS, ERS-1, ERS-2, JERS-1, and RADARSAT-1, Sentinel-1A, Sentinel-1B
        this value corresponds to the orbit count within the orbit cycle.
        For UAVSAR it is the Flight ID.
    asfFrame:
        This is primarily an ASF / JAXA frame reference. However,
        some platforms use other conventions. See ‘frame’ for ESA-centric frame searches.
    beamMode:
        The beam mode used to acquire the data.
    beamSwath:
        Encompasses a look angle and beam mode.
    campaign:
        For UAVSAR and AIRSAR data collections only. Search by general location,
        site description, or data grouping as supplied by flight agency or project.
    maxDoppler:
        Doppler provides an indication of how much the look direction deviates
        from the ideal perpendicular flight direction acquisition.
    minDoppler:
        Doppler provides an indication of how much the look direction deviates
        from the ideal perpendicular flight direction acquisition.
    end:
        End date of data acquisition. Supports timestamps
        as well as natural language such as "3 weeks ago"
    maxFaradayRotation:
        Rotation of the polarization plane of
        the radar signal impacts imagery, as HH and HV signals become mixed.
    minFaradayRotation:
        Rotation of the polarization plane of
        the radar signal impacts imagery, as HH and HV signals become mixed.
    flightDirection:
        Satellite orbit direction during data acquisition
    flightLine:
        Specify a flightline for UAVSAR or AIRSAR.
    frame:
        ESA-referenced frames are offered to give users a universal framing convention.
        Each ESA frame has a corresponding ASF frame assigned. See also: asfframe
    granule_list:
        List of specific granules.
        Search results may include several products per granule name.
    groupID:
        Identifier used to find products considered to
        be of the same scene but having different granule names
    insarStackId:
        Identifier used to find products of the same InSAR stack
    instrument:
        The instrument used to acquire the data. See also: platform
    intersectsWith:
        Search by polygon, linestring,
        or point defined in 2D Well-Known Text (WKT)
    lookDirection:
        Left or right look direction during data acquisition
    offNadirAngle:
        Off-nadir angles for ALOS PALSAR
    platform:
        Remote sensing platform that acquired the data.
        Platforms that work together, such as Sentinel-1A/1B and ERS-1/2
        have multi-platform aliases available. See also: instrument
    polarization:
        A property of SAR electromagnetic waves
        that can be used to extract meaningful information about surface properties of the earth.
    processingDate:
        Used to find data that has been processed at ASF since a given
        time and date. Supports timestamps as well as natural language such as "3 weeks ago"
    processingLevel:
        Level to which the data has been processed
    product_list:
        List of specific products.
        Guaranteed to be at most one product per product name.
    relativeOrbit:
        Path or track of satellite during data acquisition.
        For UAVSAR it is the Line ID.
    season:
        Start and end day of year for desired seasonal range.
        This option is used in conjunction with start/end to specify a seasonal range
        within an overall date range.
    start:
        Start date of data acquisition.
        Supports timestamps as well as natural language such as "3 weeks ago"
    collections:
        List of collections (concept-ids) to limit search to
    temporalBaselineDays:
        List of temporal baselines,
        used for Sentinel-1 Interferogram (BETA)
    maxResults:
        The maximum number of results to be returned by the search
    opts:
        An ASFSearchOptions object describing the search parameters to be used.
        Search parameters specified outside this object will override in event of a conflict.

    Returns
    -------
    `asf_search.ASFSearchResults` (list of search results of subclass ASFProduct)
    """
    kwargs = locals()
    data = dict((k, v) for k, v in kwargs.items() if k not in ['host', 'opts'] and v is not None)

    opts = ASFSearchOptions() if opts is None else copy(opts)
    opts.merge_args(**data)

    results = ASFSearchResults([])

    # The last page will be marked as complete if results sucessful
    perf = time.time()
    for page in search_generator(opts=opts):
        ASF_LOGGER.warning(f'Page Time Elapsed {time.time() - perf}')
        results.extend(page)
        results.searchComplete = page.searchComplete
        results.searchOptions = page.searchOptions
        perf = time.time()

    results.raise_if_incomplete()

    try:
        results.sort(key=lambda p: p.get_sort_keys(), reverse=True)
    except TypeError as exc:
        ASF_LOGGER.warning(f'Failed to sort final results, leaving results unsorted. Reason: {exc}')

    return results

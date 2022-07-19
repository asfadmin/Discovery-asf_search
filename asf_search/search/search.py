from typing import Union, Iterable, Tuple
from copy import copy
from requests.exceptions import HTTPError
from requests import Response
import datetime
import dateparser
import warnings

from asf_search import __version__

from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.CMR import build_subqueries, translate_opts
from asf_search.ASFSession import ASFSession
from asf_search.ASFProduct import ASFProduct
from asf_search.exceptions import ASFSearch4xxError, ASFSearch5xxError, ASFServerError
from asf_search.constants import INTERNAL
from asf_search.WKT.validate_wkt import validate_wkt


def search(
        absoluteOrbit: Union[int, Tuple[int, int], Iterable[Union[int, Tuple[int, int]]]] = None,
        asfFrame: Union[int, Tuple[int, int], Iterable[Union[int, Tuple[int, int]]]] = None,
        beamMode: Union[str, Iterable[str]] = None,
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
        maxResults: int = None,
        opts: ASFSearchOptions = None,
) -> ASFSearchResults:
    """
    Performs a generic search using the ASF SearchAPI. Accepts a number of search parameters, and/or an ASFSearchOptions object. If an ASFSearchOptions object is provided as well as other specific parameters, the two sets of options will be merged, preferring the specific keyword arguments.

    :param absoluteOrbit: For ALOS, ERS-1, ERS-2, JERS-1, and RADARSAT-1, Sentinel-1A, Sentinel-1B this value corresponds to the orbit count within the orbit cycle. For UAVSAR it is the Flight ID.
    :param asfFrame: This is primarily an ASF / JAXA frame reference. However, some platforms use other conventions. See ‘frame’ for ESA-centric frame searches.
    :param beamMode: The beam mode used to acquire the data.
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

    # Create a kwargs dict, that's all of the 'not None' items, and merge it with opts:
    kwargs = locals()
    opts = (ASFSearchOptions() if kwargs["opts"] is None else copy(opts))
    del kwargs["opts"]

    kwargs = dict((k, v) for k, v in kwargs.items() if v is not None)
    kw_opts = ASFSearchOptions(**kwargs)

    # Anything passed in as kwargs has priority over anything in opts:
    opts.merge_args(**dict(kw_opts))

    maxResults = opts.pop("maxResults", None)

    if maxResults is not None and \
        (getattr(opts, 'granule_list', False) or getattr(opts, 'product_list', False)):
            raise ValueError("Cannot use maxResults along with product_list/granule_list.")

    preprocess_opts(opts)

    url = '/'.join(s.strip('/') for s in [f'https://{INTERNAL.CMR_HOST}', f'{INTERNAL.CMR_GRANULE_PATH}'])

    results = ASFSearchResults(opts=opts)

    for query in build_subqueries(opts):
        translated_opts = translate_opts(query)

        response = get_page(session=opts.session, url=url, translated_opts=translated_opts)

        hits = [ASFProduct(f, session=query.session) for f in response.json()['items']]

        if maxResults != None:
            results.extend(hits[:min(maxResults - len(results), len(hits))])
            if len(results) == maxResults:
                break
        else:
            results.extend(hits)

        while('CMR-Search-After' in response.headers):
            opts.session.headers.update({'CMR-Search-After': response.headers['CMR-Search-After']})

            response = get_page(session=opts.session, url=url, translated_opts=translated_opts)

            hits = [ASFProduct(f, session=query.session) for f in response.json()['items']]
            
            if maxResults != None:
                results.extend(hits[:min(maxResults - len(results), len(hits))])
                if len(results) == maxResults:
                    break
            else:
                results.extend(hits)
        
        opts.session.headers.pop('CMR-Search-After', None)

    results.sort(key=lambda p: (p.properties['stopTime'], p.properties['fileID']), reverse=True)
    return results

def get_page(session: ASFSession, url: str, translated_opts: list) -> Response:
    response = session.post(url=url, data=translated_opts)
    try:
        response.raise_for_status()
    except HTTPError:
        if 400 <= response.status_code <= 499:
            raise ASFSearch4xxError(f'HTTP {response.status_code}: {response.json()["errors"]}')
        if 500 <= response.status_code <= 599:
            raise ASFSearch5xxError(f'HTTP {response.status_code}: {response.json()["errors"]}')
        raise ASFServerError(f'HTTP {response.status_code}: {response.json()["errors"]}')
    
    return response


def preprocess_opts(opts: ASFSearchOptions):
    # Repair WKT here so it only happens once, and you can save the result to the new Opts object:
    wrap_wkt(opts=opts)

    # Date/Time logic, convert "today" to the literal timestamp if needed:
    set_default_dates(opts=opts)

    # Platform Alias logic:
    set_platform_alias(opts=opts)


def wrap_wkt(opts: ASFSearchOptions):
    if opts.intersectsWith is not None:
        opts.intersectsWith = validate_wkt(opts.intersectsWith).wkt


def set_default_dates(opts: ASFSearchOptions):
    if opts.start is not None and isinstance(opts.start, str):
        opts.start = dateparser.parse(opts.start, settings={'RETURN_AS_TIMEZONE_AWARE': True})
    if opts.end is not None and isinstance(opts.end, str):
        opts.end = dateparser.parse(opts.end, settings={'RETURN_AS_TIMEZONE_AWARE': True})
    # If both are used, make sure they're in the right order:
    if opts.start is not None and opts.end is not None:
        if opts.start > opts.end:
            warnings.warn(f"Start date ({opts.start}) is after end date ({opts.end}). Switching the two.")
            opts.start, opts.end = opts.end, opts.start
    # Can't do this sooner, since you need to compare start vs end:
    if opts.start is not None:
        opts.start = opts.start.strftime('%Y-%m-%dT%H:%M:%SZ')
    if opts.end is not None:
        opts.end = opts.end.strftime('%Y-%m-%dT%H:%M:%SZ')


def set_platform_alias(opts: ASFSearchOptions):
    # Platform Alias logic:
    if opts.platform is not None:
        plat_aliases = {
            # Groups:
            'S1': ['SENTINEL-1A', 'SENTINEL-1B'],
            'SENTINEL-1': ['SENTINEL-1A', 'SENTINEL-1B'],
            'SENTINEL': ['SENTINEL-1A', 'SENTINEL-1B'],
            'ERS': ['ERS-1', 'ERS-2'],
            'SIR-C': ['STS-59', 'STS-68'],
            # Singles / Aliases:
            'R1': ['RADARSAT-1'],
            'E1': ['ERS-1'],
            'E2': ['ERS-2'],
            'J1': ['JERS-1'],
            'A3': ['ALOS'],
            'AS': ['DC-8'],
            'AIRSAR': ['DC-8'],
            'SS': ['SEASAT 1'],
            'SEASAT': ['SEASAT 1'],
            'SA': ['SENTINEL-1A'],
            'SB': ['SENTINEL-1B'],
            'SP': ['SMAP'],
            'UA': ['G-III'],
            'UAVSAR': ['G-III'],
        }
        platform_list = []
        for plat in opts.platform:
            # If it's a key, *replace* it with all the values. Else just add the key:
            if plat.upper() in plat_aliases:
                platform_list.extend(plat_aliases[plat.upper()])
            else:
                platform_list.append(plat)

        opts.platform = list(set(platform_list))

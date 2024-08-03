import time
from typing import Dict, Generator, Union, Sequence, Tuple, List
from copy import copy
from requests.exceptions import HTTPError
from requests import ReadTimeout, Response
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)
import datetime
import dateparser

from asf_search import ASF_LOGGER

from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.CMR import build_subqueries, translate_opts
from asf_search.CMR.datasets import dataset_collections

from asf_search.ASFSession import ASFSession
from asf_search.ASFProduct import ASFProduct
from asf_search.exceptions import (
    ASFSearch4xxError,
    ASFSearch5xxError,
    ASFSearchError,
    CMRIncompleteError,
)
from asf_search.constants import INTERNAL
from asf_search.WKT.validate_wkt import validate_wkt
from asf_search.search.error_reporting import report_search_error
import asf_search.Products as ASFProductType


def search_generator(
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
) -> Generator[ASFSearchResults, None, None]:
    """
    Performs a generic search against the Central Metadata Repository (CMR),
    yielding results page by page (250 products at a time by default) as they're returned from CMR.

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

    Yields
    -------
    `asf_search.ASFSearchResults` (list of search results of subclass ASFProduct, page by page)
    """

    # Create a kwargs dict, that's all of the 'not None' items, and merge it with opts:
    kwargs = locals()
    opts = ASFSearchOptions() if kwargs['opts'] is None else copy(opts)
    del kwargs['opts']

    kwargs = dict((k, v) for k, v in kwargs.items() if v is not None)
    kw_opts = ASFSearchOptions(**kwargs)

    # Anything passed in as kwargs has priority over anything in opts:
    opts.merge_args(**dict(kw_opts))

    maxResults = opts.pop('maxResults', None)

    if maxResults is not None and (
        getattr(opts, 'granule_list', False) or getattr(opts, 'product_list', False)
    ):
        raise ValueError('Cannot use maxResults along with product_list/granule_list.')

    ASF_LOGGER.debug(f'SEARCH: preprocessing opts: {opts}')
    preprocess_opts(opts)
    ASF_LOGGER.debug(f'SEARCH: preprocessed opts: {opts}')

    ASF_LOGGER.info(f'SEARCH: Using search opts {opts}')

    url = '/'.join(s.strip('/') for s in [f'https://{opts.host}', f'{INTERNAL.CMR_GRANULE_PATH}'])
    total = 0

    queries = build_subqueries(opts)

    ASF_LOGGER.info(f'SEARCH: Using cmr endpoint: "{url}"')
    ASF_LOGGER.debug(f'SEARCH: Built {len(queries)} subqueries')

    for subquery_idx, query in enumerate(queries):
        ASF_LOGGER.info(f'SUBQUERY {subquery_idx + 1}: Beginning subquery with opts: {query}')

        ASF_LOGGER.debug(f'TRANSLATION: Translating subquery:\n{query}')
        translated_opts = translate_opts(query)
        ASF_LOGGER.debug(f'TRANSLATION: Subquery translated to cmr keywords:\n{translated_opts}')
        cmr_search_after_header = ''
        subquery_count = 0

        page_number = 1
        while cmr_search_after_header is not None:
            try:
                ASF_LOGGER.debug(f'SUBQUERY {subquery_idx + 1}: Fetching page {page_number}')
                items, subquery_max_results, cmr_search_after_header = query_cmr(
                    opts.session, url, translated_opts, subquery_count
                )
            except (ASFSearchError, CMRIncompleteError) as exc:
                message = str(exc)
                ASF_LOGGER.error(message)
                report_search_error(query, message)
                opts.session.headers.pop('CMR-Search-After', None)
                # If it's a CMRIncompleteError, we can just stop here and return what we have
                # It's up to the user to call .raise_if_incomplete() if they're using the
                # generator directly.
                if isinstance(exc, CMRIncompleteError):
                    return
                else:
                    raise

            ASF_LOGGER.debug(
                f'SUBQUERY {subquery_idx + 1}: Page {page_number} fetched, returned {len(items)} items.'
            )
            opts.session.headers.update({'CMR-Search-After': cmr_search_after_header})
            perf = time.time()
            last_page = process_page(
                items, maxResults, subquery_max_results, total, subquery_count, opts
            )
            ASF_LOGGER.warning(f'Page Processing Time {time.time() - perf}')
            subquery_count += len(last_page)
            total += len(last_page)
            last_page.searchComplete = subquery_count == subquery_max_results or total == maxResults
            yield last_page

            if last_page.searchComplete:
                if total == maxResults:  # the user has as many results as they wanted
                    ASF_LOGGER.info(f'SEARCH COMPLETE: MaxResults ({maxResults}) reached')
                    opts.session.headers.pop('CMR-Search-After', None)
                    return
                else:  # or we've gotten all possible results for this subquery
                    ASF_LOGGER.info(
                        f'SUBQUERY {subquery_idx + 1} COMPLETE: results exhausted for subquery'
                    )
                    cmr_search_after_header = None

            page_number += 1

        opts.session.headers.pop('CMR-Search-After', None)

    ASF_LOGGER.info(f'SEARCH COMPLETE: results exhausted for search opts {opts}')


@retry(
    reraise=True,
    retry=retry_if_exception_type(CMRIncompleteError),
    wait=wait_fixed(2),
    stop=stop_after_attempt(3),
)
def query_cmr(
    session: ASFSession,
    url: str,
    translated_opts: Dict,
    sub_query_count: int,
):
    response = get_page(session=session, url=url, translated_opts=translated_opts)

    perf = time.time()
    items = [as_ASFProduct(f, session=session) for f in response.json()['items']]
    ASF_LOGGER.warning(f'Product Subclassing Time {time.time() - perf}')
    hits: int = response.json()['hits']  # total count of products given search opts
    # 9-10 per process
    # 3.9-5 per process
    # sometimes CMR returns results with the wrong page size
    if len(items) != INTERNAL.CMR_PAGE_SIZE and len(items) + sub_query_count < hits:
        raise CMRIncompleteError(
            'CMR returned page of incomplete results.'
            f'Expected {min(INTERNAL.CMR_PAGE_SIZE, hits - sub_query_count)} results,'
            f'got {len(items)}'
        )

    return items, hits, response.headers.get('CMR-Search-After', None)


def process_page(
    items: List[ASFProduct],
    max_results: int,
    subquery_max_results: int,
    total: int,
    subquery_count: int,
    opts: ASFSearchOptions,
):
    if max_results is None:
        last_page = ASFSearchResults(
            items[: min(subquery_max_results - subquery_count, len(items))], opts=opts
        )
    else:
        last_page = ASFSearchResults(items[: min(max_results - total, len(items))], opts=opts)
    return last_page


@retry(
    reraise=True,
    retry=retry_if_exception_type(ASFSearch5xxError),
    wait=wait_exponential(
        multiplier=1, min=3, max=10
    ),  # Wait 2^x * 1 starting with 3 seconds, max 10 seconds between retries
    stop=stop_after_attempt(3),
)
def get_page(session: ASFSession, url: str, translated_opts: List) -> Response:
    from asf_search.constants.INTERNAL import CMR_TIMEOUT

    perf = time.time()
    try:
        response = session.post(url=url, data=translated_opts, timeout=CMR_TIMEOUT)
        response.raise_for_status()
    except HTTPError as exc:
        error_message = f'HTTP {response.status_code}: {response.json()["errors"]}'
        if 400 <= response.status_code <= 499:
            raise ASFSearch4xxError(error_message) from exc
        if 500 <= response.status_code <= 599:
            raise ASFSearch5xxError(error_message) from exc
    except ReadTimeout as exc:
        raise ASFSearchError(
            f'Connection Error (Timeout): CMR took too long to respond. Set asf constant "asf_search.constants.INTERNAL.CMR_TIMEOUT" to increase. ({url=}, timeout={CMR_TIMEOUT})'
        ) from exc

    ASF_LOGGER.warning(f'Query Time Elapsed {time.time() - perf}')
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
        wrapped, _, repairs = validate_wkt(opts.intersectsWith)
        opts.intersectsWith = wrapped.wkt
        if len(repairs):
            ASF_LOGGER.warning(
                'WKT REPAIR/VALIDATION: The following repairs were performed'
                f'on the provided AOI:\n{[str(repair) for repair in repairs]}'
            )


def set_default_dates(opts: ASFSearchOptions):
    if opts.start is not None and isinstance(opts.start, str):
        opts.start = dateparser.parse(opts.start, settings={'RETURN_AS_TIMEZONE_AWARE': True})
    if opts.end is not None and isinstance(opts.end, str):
        opts.end = dateparser.parse(opts.end, settings={'RETURN_AS_TIMEZONE_AWARE': True})
    # If both are used, make sure they're in the right order:
    if opts.start is not None and opts.end is not None:
        if opts.start > opts.end:
            ASF_LOGGER.warning(
                f'Start date ({opts.start}) is after end date ({opts.end}). Switching the two.'
            )
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


_dataset_collection_items = dataset_collections.items()


def as_ASFProduct(item: Dict, session: ASFSession) -> ASFProduct:
    """Returns the granule umm as the corresponding ASFProduct subclass,
    or ASFProduct if no equivalent is found

    :param item: the granule umm json
    :param session: the session used to query CMR for the product

    :returns the granule as an object of type ASFProduct
    """
    if ASFProductType.OPERAS1Product._is_subclass(item):
        return ASFProductType.OPERAS1Product(item, session=session)

    product_type_key = _get_product_type_key(item)

    # if there's a direct entry in our dataset to product type dict
    # perf = time.time()
    subclass = dataset_to_product_types.get(product_type_key)
    if subclass is not None:
        # ASF_LOGGER.warning(f'subclass selection time {time.time() - perf}')
        return subclass(item, session=session)

    # if the key matches one of the shortnames in any of our datasets
    for dataset, collections in _dataset_collection_items:
        if collections.get(product_type_key) is not None:
            subclass = dataset_to_product_types.get(dataset)
            if subclass is not None:
                # ASF_LOGGER.warning(f'subclass selection time {time.time() - perf}')
                return subclass(item, session=session)
            break  # dataset exists, but is not in dataset_to_product_types yet

    # If the platform exists, try to match it
    platform = _get_platform(item=item)
    if ASFProductType.ARIAS1GUNWProduct._is_subclass(item=item):
        return dataset_to_product_types.get('ARIA S1 GUNW')(item, session=session)
    elif (subclass := dataset_to_product_types.get(platform)) is not None:
        return subclass(item, session=session)

    output = ASFProduct(item, session=session)

    granule_concept_id = output.meta.get('concept-id', 'Missing Granule Concept ID')
    fileID = output.properties.get(
        'fileID', output.properties.get('sceneName', 'fileID and sceneName Missing')
    )

    ASF_LOGGER.warning(
        f'Failed to find corresponding ASFProduct subclass for \
        Product: "{fileID}", Granule Concept ID: "{granule_concept_id}", \
        default to "ASFProduct"'
    )
    return output


def _get_product_type_key(item: Dict) -> str:
    """Match the umm response to the right ASFProduct subclass by returning one of the following:
    1. collection shortName (Ideal case)
    2. platform_shortName (Fallback)
        - special case: Aria S1 GUNW
    """
    collection_shortName = ASFProduct.umm_get(item['umm'], 'CollectionReference', 'ShortName')

    if collection_shortName is None:
        if ASFProductType.ARIAS1GUNWProduct._is_subclass(item=item):
            return 'ARIA S1 GUNW'

        platform = _get_platform(item=item)
        return platform

    return collection_shortName


def _get_platform(item: Dict):
    return ASFProduct.umm_get(item['umm'], 'Platforms', 0, 'ShortName')


# Maps datasets from DATASET.py and collection/platform shortnames to ASFProduct subclasses
dataset_to_product_types = {
    'SENTINEL-1': ASFProductType.S1Product,
    'OPERA-S1': ASFProductType.OPERAS1Product,
    'OPERA-S1-CALVAL': ASFProductType.OPERAS1Product,
    'SLC-BURST': ASFProductType.S1BurstProduct,
    'ALOS': ASFProductType.ALOSProduct,
    'SIR-C': ASFProductType.SIRCProduct,
    'STS-59': ASFProductType.SIRCProduct,
    'STS-68': ASFProductType.SIRCProduct,
    'ARIA S1 GUNW': ASFProductType.ARIAS1GUNWProduct,
    'SMAP': ASFProductType.SMAPProduct,
    'UAVSAR': ASFProductType.UAVSARProduct,
    'G-III': ASFProductType.UAVSARProduct,
    'RADARSAT-1': ASFProductType.RADARSATProduct,
    'ERS': ASFProductType.ERSProduct,
    'ERS-1': ASFProductType.ERSProduct,
    'ERS-2': ASFProductType.ERSProduct,
    'JERS-1': ASFProductType.JERSProduct,
    'AIRSAR': ASFProductType.AIRSARProduct,
    'DC-8': ASFProductType.AIRSARProduct,
    'SEASAT': ASFProductType.SEASATProduct,
    'SEASAT 1': ASFProductType.SEASATProduct,
    'NISAR': ASFProductType.NISARProduct,
}

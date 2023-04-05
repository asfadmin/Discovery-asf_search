import logging
from typing import Generator, Union, Iterable, Tuple
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
from asf_search.exceptions import ASFError, ASFSearch4xxError, ASFSearch5xxError, ASFSearchError, ASFServerError
from asf_search.constants import INTERNAL
from asf_search.WKT.validate_wkt import validate_wkt
from asf_search.search.error_reporting import report_search_error


def search_generator(        
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
        ) -> Generator[ASFSearchResults, None, None]:
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

    url = '/'.join(s.strip('/') for s in [f'https://{opts.host}', f'{INTERNAL.CMR_GRANULE_PATH}'])
    count = 0
    
    for query in build_subqueries(opts):
        translated_opts = translate_opts(query)
        try:
            response = get_page(session=opts.session, url=url, translated_opts=translated_opts, search_opts=query)
        except ASFError as e:
            logging.error(str(e))
            opts.session.headers.pop('CMR-Search-After', None)
            return

        hits = [ASFProduct(f, session=query.session) for f in response.json()['items']]

        if 'CMR-Search-After' in response.headers:
            opts.session.headers.update({'CMR-Search-After': response.headers['CMR-Search-After']})

        if maxResults != None:
            last_page = ASFSearchResults(hits[:min(maxResults - count, len(hits))], opts=opts)
            count += len(last_page)
            
            if count == maxResults:
                last_page.searchComplete = True
                yield last_page
                return
            else:
                yield last_page
        else:
            count += len(hits)
            yield ASFSearchResults(hits, opts=opts)

        while('CMR-Search-After' in response.headers):
            opts.session.headers.update({'CMR-Search-After': response.headers['CMR-Search-After']})

            try:
                response = get_page(session=opts.session, url=url, translated_opts=translated_opts, search_opts=query)
            except ASFError as e:
                logging.error(str(e))
                opts.session.headers.pop('CMR-Search-After', None)
                return

            hits = [ASFProduct(f, session=query.session) for f in response.json()['items']]

            if len(hits):
                if maxResults != None:
                    last_page = ASFSearchResults(hits[:min(maxResults - count, len(hits))], opts=opts)
                    count += len(last_page)
                    # results.extend(hits[:min(maxResults - len(results), len(hits))])
                    if count == maxResults:
                        last_page.searchComplete = True
                        yield last_page
                        return
                    else:
                        yield last_page
                else:
                    count += len(hits)
                    yield ASFSearchResults(hits, opts=opts)

        opts.session.headers.pop('CMR-Search-After', None)

def get_page(session: ASFSession, url: str, translated_opts: list, search_opts: ASFSearchOptions) -> Response:
    max_retries = 3
    error_message = ''

    for _ in range(max_retries):
        response = session.post(url=url, data=translated_opts, timeout=170)

        try:
            response.raise_for_status()
        except HTTPError:
            error_message = f'HTTP {response.status_code}: {response.json()["errors"]}'
            if 400 <= response.status_code <= 499:
                error = ASFSearch4xxError(error_message)
            if 500 <= response.status_code <= 599:
                error = ASFSearch5xxError(error_message)
        else:
            return response
    
    report_search_error(search_opts, error_message)
    raise error


def preprocess_opts(opts: ASFSearchOptions):
    # Repair WKT here so it only happens once, and you can save the result to the new Opts object:
    wrap_wkt(opts=opts)

    # Date/Time logic, convert "today" to the literal timestamp if needed:
    set_default_dates(opts=opts)

    # Platform Alias logic:
    set_platform_alias(opts=opts)


def wrap_wkt(opts: ASFSearchOptions):
    if opts.intersectsWith is not None:
        wrapped, _, __ = validate_wkt(opts.intersectsWith)
        opts.intersectsWith = wrapped.wkt


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

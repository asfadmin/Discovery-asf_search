import datetime
from typing import Iterable, Tuple, Union
from copy import copy
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.CMR.subquery import build_subqueries
from asf_search.CMR import translate_opts
from asf_search.search.search_generator import get_page, preprocess_opts
from asf_search import INTERNAL


def search_count(        
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
        maxResults: int = None,
        opts: ASFSearchOptions = None,
) -> int:
    # Create a kwargs dict, that's all of the 'not None' items, and merge it with opts:
    kwargs = locals()
    opts = (ASFSearchOptions() if kwargs["opts"] is None else copy(opts))
    del kwargs["opts"]

    kwargs = dict((k, v) for k, v in kwargs.items() if v is not None)
    kw_opts = ASFSearchOptions(**kwargs)

    # Anything passed in as kwargs has priority over anything in opts:
    opts.merge_args(**dict(kw_opts))

    preprocess_opts(opts)

    url = '/'.join(s.strip('/') for s in [f'https://{opts.host}', f'{INTERNAL.CMR_GRANULE_PATH}'])

    count = 0
    for query in build_subqueries(opts):
        translated_opts = translate_opts(query)
        idx = translated_opts.index(('page_size', INTERNAL.CMR_PAGE_SIZE))
        translated_opts[idx] = ('page_size', 0)
        
        response = get_page(session=opts.session, url=url, translated_opts=translated_opts, search_opts=query)
        count += response.json()['hits']
    return count

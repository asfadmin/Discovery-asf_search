from dateutil.parser import parse
import pytz
from copy import copy

from asf_search.search import search, product_search
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.ASFProduct import ASFProduct
from asf_search.ASFSession import ASFSession
from asf_search.constants import PLATFORM
from asf_search.exceptions import ASFSearchError, ASFBaselineError


precalc_platforms = [
    PLATFORM.ALOS,
    PLATFORM.RADARSAT,
    PLATFORM.ERS1,
    PLATFORM.ERS2,
    PLATFORM.JERS,
]


def stack_from_product(
        reference: ASFProduct,
        cmr_provider: str = None,
        session: ASFSession = None,
        opts: ASFSearchOptions = None,
        host: str = None
    ) -> ASFSearchResults:
    """
    Finds a baseline stack from a reference ASFProduct

    :param reference: Reference scene to base the stack on, and from which to calculate perpendicular/temporal baselines
    :param cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider
    :param session: A Session to be used when performing the search. For most uses, can be ignored. Used when searching for a dataset, provider, etc. that requires authentication. See also: asf_search.ASFSession
    :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes and can generally be ignored.

    :return: ASFSearchResults(dict) of search results
    """

    kwargs = locals()
    data = dict((k, v) for k, v in kwargs.items() if k not in ['host', 'opts', 'reference'] and v is not None)

    opts = (ASFSearchOptions() if opts is None else copy(opts))
    for p in data:
        setattr(opts, p, data[p])

    stack_opts = get_stack_opts(reference, opts=opts)

    stack = search(opts=stack_opts, host=host)
    calc_temporal_baselines(reference, stack)
    stack.sort(key=lambda product: product.properties['temporalBaseline'])

    return stack


def stack_from_id(
        reference_id: str,
        cmr_provider: str = None,
        session: ASFSession = None,
        opts: ASFSearchOptions = None,
        host: str = None
    ) -> ASFSearchResults:
    """
    Finds a baseline stack from a reference product ID

    :param reference_id: Reference product to base the stack from, and from which to calculate perpendicular/temporal baselines
    :param cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider
    :param session: A Session to be used when performing the search. For most uses, can be ignored. Used when searching for a dataset, provider, etc. that requires authentication. See also: asf_search.ASFSession
    :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes and can generally be ignored.

    :return: ASFSearchResults(list) of search results
    """
    kwargs = locals()
    data = dict((k, v) for k, v in kwargs.items() if k not in ['host', 'opts', 'reference_id'] and v is not None)

    opts = (ASFSearchOptions() if opts is None else copy(opts))
    for p in data:
        setattr(opts, p, data[p])

    reference_results = product_search(product_list=reference_id, opts=opts, host=host)

    if len(reference_results) <= 0:
        raise ASFSearchError(f'Reference product not found: {reference_id}')
    reference = reference_results[0]

    return stack_from_product(reference, host=host, session=session, cmr_provider=cmr_provider)


def get_stack_opts(reference: ASFProduct, opts: ASFSearchOptions = None) -> ASFSearchOptions:

    stack_opts = (ASFSearchOptions() if opts is None else copy(opts))
    stack_opts.processingLevel = reference.properties['processingLevel']

    if reference.properties['platform'] in precalc_platforms:
        if reference.properties['insarStackId'] not in [None, 'NA', 0, '0']:
            stack_opts.insarStackId = reference.properties['insarStackId']
            return stack_opts
        raise ASFBaselineError(f'Requested reference product needs a baseline stack ID but does not have one: {reference["properties"]["fileID"]}')

    # build a stack from scratch if it's a non-precalc dataset with state vectors
    if reference.properties['platform'] in [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B]:
        stack_opts.platform = [PLATFORM.SENTINEL1]
        stack_opts.beamMode = [reference.properties['beamModeType']]
        stack_opts.flightDirection = reference.properties['flightDirection']
        stack_opts.relativeOrbit = [int(reference.properties['pathNumber'])]  # path
        if reference.properties['polarization'] in ['HH', 'HH+HV']:
            stack_opts.polarization = ['HH','HH+HV']
        elif reference.properties['polarization'] in ['VV', 'VV+VH']:
            stack_opts.polarization = ['VV','VV+VH']
        else:
            stack_opts.polarization = [reference.properties['polarization']]
        stack_opts.intersectsWith = reference.centroid().wkt
        return stack_opts

    raise ASFBaselineError(f'Reference product is not a pre-calculated baseline dataset, and not a known ephemeris-based dataset: {reference.properties["fileID"]}')


def calc_temporal_baselines(reference: ASFProduct, stack: ASFSearchResults) -> None:
    """
    Calculates temporal baselines for a stack of products based on a reference scene and injects those values into the stack.

    :param reference: The reference product from which to calculate temporal baselines.
    :param stack: The stack to operate on.
    :return: None, as the operation occurs in-place on the stack provided.
    """
    reference_time = parse(reference.properties['startTime'])
    if reference_time.tzinfo is None:
        reference_time = pytz.utc.localize(reference_time)

    for secondary in stack:
        secondary_time = parse(secondary.properties['startTime'])
        if secondary_time.tzinfo is None:
            secondary_time = pytz.utc.localize(secondary_time)
        secondary.properties['temporalBaseline'] = (secondary_time - reference_time).days

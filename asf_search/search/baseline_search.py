from asf_search.baseline.stack import get_baseline_from_stack, get_default_product_type
from copy import copy

from asf_search.search import search, product_search
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.ASFProduct import ASFProduct
from asf_search.constants import PLATFORM
from asf_search.exceptions import ASFSearchError, ASFBaselineError
from copy import copy

precalc_platforms = [
    PLATFORM.ALOS,
    PLATFORM.RADARSAT,
    PLATFORM.ERS1,
    PLATFORM.ERS2,
    PLATFORM.JERS,
]


def stack_from_product(
        reference: ASFProduct,
        opts: ASFSearchOptions = None
    ) -> ASFSearchResults:
    """
    Finds a baseline stack from a reference ASFProduct

    :param reference: Reference scene to base the stack on, and from which to calculate perpendicular/temporal baselines
    :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.

    :return: ASFSearchResults(dict) of search results
    """

    opts = (ASFSearchOptions() if opts is None else copy(opts))

    stack_opts = get_stack_opts(reference, opts=opts)

    stack = search(opts=stack_opts)
    stack, warnings = get_baseline_from_stack(reference=reference, stack=stack)
    # calc_temporal_baselines(reference, stack)
    stack.sort(key=lambda product: product.properties['temporalBaseline'])

    return stack

def stack_from_id(
        reference_id: str,
        opts: ASFSearchOptions = None
) -> ASFSearchResults:
    """
    Finds a baseline stack from a reference product ID

    :param reference_id: Reference product to base the stack from, and from which to calculate perpendicular/temporal baselines
    :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.

    :return: ASFSearchResults(list) of search results
    """

    opts = (ASFSearchOptions() if opts is None else copy(opts))

    reference_results = product_search(product_list=reference_id, opts=opts)

    if len(reference_results) <= 0:
        raise ASFSearchError(f'Reference product not found: {reference_id}')
    reference = reference_results[0]

    return stack_from_product(reference, opts=opts)


def get_stack_opts(
        reference: ASFProduct,
        opts: ASFSearchOptions = None
) -> ASFSearchOptions:

    stack_opts = (ASFSearchOptions() if opts is None else copy(opts))
    stack_opts.processingLevel = get_default_product_type(reference.properties['sceneName'])

    if reference.properties['platform'] in precalc_platforms:
        if reference.properties['insarStackId'] not in [None, 'NA', 0, '0']:
            stack_opts.insarStackId = reference.properties['insarStackId']
            return stack_opts
        raise ASFBaselineError(f'Requested reference product needs a baseline stack ID but does not have one: {reference.properties["fileID"]}')

    # build a stack from scratch if it's a non-precalc dataset with state vectors
    if reference.properties['platform'] in [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B]:
        stack_opts.platform = [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B]
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

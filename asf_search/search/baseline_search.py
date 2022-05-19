from asf_search.baseline.stack import get_baseline_from_stack
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
        opts: ASFSearchOptions = None
    ) -> ASFSearchResults:
    """
    Finds a baseline stack from a reference ASFProduct

    :param reference: Reference scene to base the stack on, and from which to calculate perpendicular/temporal baselines
    :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.

    :return: ASFSearchResults(dict) of search results
    """

#<<<<<<< master
    stack_params = get_stack_params(reference)
    stack = search(**stack_params, host=host, cmr_token=cmr_token, cmr_provider=cmr_provider)
    stack, warnings = get_baseline_from_stack(reference=reference, stack=stack)

#=======
    opts = (ASFSearchOptions() if opts is None else copy(opts))

    stack_opts = get_stack_opts(reference, opts=opts)

    stack = search(opts=stack_opts)
    calc_temporal_baselines(reference, stack)
#>>>>>>> options-validation-object
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
    stack_opts.processingLevel = reference.properties['processingLevel']

    if reference.properties['platform'] in precalc_platforms:
        if reference.properties['insarStackId'] not in [None, 'NA', 0, '0']:
#<<<<<<< master
            stack_params['insarStackId'] = reference.properties['insarStackId']
            return stack_params
        raise ASFBaselineError(f'Requested reference product needs a baseline stack ID but does not have one: {reference.properties["fileID"]}')
#=======
            stack_opts.insarStackId = reference.properties['insarStackId']
            return stack_opts
        raise ASFBaselineError(f'Requested reference product needs a baseline stack ID but does not have one: {reference["properties"]["fileID"]}')
#>>>>>>> options-validation-object

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


def calc_temporal_baselines(
        reference: ASFProduct,
        stack: ASFSearchResults
) -> None:
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

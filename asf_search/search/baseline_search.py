from dateutil.parser import parse
import pytz

from asf_search.search import search
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.ASFProduct import ASFProduct
from asf_search.search.product_search import product_search
from asf_search.constants import INTERNAL, PLATFORM
from asf_search.exceptions import ASFSearchError, ASFBaselineError


precalc_platforms = [
    PLATFORM.ALOS,
    PLATFORM.RADARSAT,
    PLATFORM.ERS1,
    PLATFORM.ERS2,
    PLATFORM.JERS]


def stack_from_product(
        reference: ASFProduct,
        strategy = None,
        host: str = INTERNAL.SEARCH_API_HOST,
        cmr_token: str = None,
        cmr_provider: str = None) -> ASFSearchResults:
    """
    Finds a baseline stack from a reference ASFProduct

    :param reference: Reference scene to base the stack from, and from which to calculate perpendicular/temporal baselines
    :param strategy: If the requested reference can not be used to calculate perpendicular baselines, this sort function will be used to pick an alternative reference from the stack. 'None' implies that no attempt will be made to find an alternative reference.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :param cmr_token: EDL Auth Token for authenticated searches, see https://urs.earthdata.nasa.gov/user_tokens
    :param cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider

    :return: ASFSearchResults(dict) of search results
    """

    stack_params = get_stack_params(reference)
    stack = search(**stack_params, host=host, cmr_token=cmr_token, cmr_provider=cmr_provider)
    calc_temporal_baselines(reference, stack)
    stack.sort(key=lambda product: product.properties['temporalBaseline'])

    return stack


def stack_from_id(
        reference_id: str,
        strategy = None,
        host: str = INTERNAL.SEARCH_API_HOST,
        cmr_token: str = None,
        cmr_provider: str = None) -> ASFSearchResults:
    """
    Finds a baseline stack from a reference product ID

    :param reference_id: Reference product to base the stack from, and from which to calculate perpendicular/temporal baselines
    :param strategy: If the requested reference can not be used to calculate perpendicular baselines, this sort function will be used to pick an alternative reference from the stack. 'None' implies that no attempt will be made to find an alternative reference.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :param cmr_token: EDL Auth Token for authenticated searches, see https://urs.earthdata.nasa.gov/user_tokens
    :param cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider

    :return: ASFSearchResults(list) of search results
    """
    reference_results = product_search(
        [reference_id],
        host=host,
        cmr_token=cmr_token,
        cmr_provider=cmr_provider)

    if len(reference_results) <= 0:
        raise ASFSearchError(f'Reference product not found: {reference_id}')
    reference = reference_results[0]

    return stack_from_product(reference, host=host, cmr_token=cmr_token, cmr_provider=cmr_provider)


def get_stack_params(reference: ASFProduct) -> dict:

    stack_params = {
        'processingLevel': [reference.properties['processingLevel']]
    }

    if reference.properties['platform'] in precalc_platforms:
        if reference.properties['insarStackId'] not in [None, 'NA', 0, '0']:
            stack_params['insarStackId'] = reference.properties['insarStackId']
            return stack_params
        raise ASFBaselineError(f'Requested reference product needs a baseline stack ID but does not have one: {reference["properties"]["fileID"]}')

    # build a stack from scratch if it's a non-precalc dataset with state vectors
    if reference.properties['platform'] in [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B]:
        stack_params['platform'] = [PLATFORM.SENTINEL1]
        stack_params['beamMode'] = [reference.properties['beamModeType']]
        stack_params['flightDirection'] = [reference.properties['flightDirection']]
        #stack_params['lookDirection'] = [ref_scene.properties['lookDirection']]
        stack_params['relativeOrbit'] = [int(reference.properties['pathNumber'])]  # path
        if reference.properties['polarization'] in ['HH', 'HH+HV']:
            stack_params['polarization'] = ['HH','HH+HV']
        elif reference.properties['polarization'] in ['VV', 'VV+VH']:
            stack_params['polarization'] = ['VV','VV+VH']
        else:
            stack_params['polarization'] = [reference.properties['polarization']]
        stack_params['intersectsWith'] = reference.centroid().wkt
        return stack_params

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

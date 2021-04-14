from typing import Iterable
import numpy as np
from .search import search
from .results import ASFSearchResults
from .product import ASFProduct
from .product_search import product_search
from ..constants import INTERNAL, PLATFORM
from ..exceptions import ASFSearchError, ASFBaselineError


precalc_platforms = [
    PLATFORM.ALOS,
    PLATFORM.RADARSAT,
    PLATFORM.ERS1,
    PLATFORM.ERS2,
    PLATFORM.JERS]


def stack_from_product(
        reference: ASFProduct,
        strategy = None,
        host: str = INTERNAL.HOST,
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
    stack_results = search(**stack_params, host=host, cmr_token=cmr_token, cmr_provider=cmr_provider)
    calc_temporal_baselines(reference, stack_results)

    #TODO: Calculate temporal baselines
    #TODO: Calculate perpendicular baselines
    #TODO: Add nearest neighbor finder

    return stack_results


def stack_from_id(
        reference_id: str,
        strategy = None,
        host: str = INTERNAL.HOST,
        cmr_token: str = None,
        cmr_provider: str = None) -> ASFSearchResults:
    """
    Finds a baseline stack from a reference product ID

    :param reference_id: Reference product to base the stack from, and from which to calculate perpendicular/temporal baselines
    :param strategy: If the requested reference can not be used to calculate perpendicular baselines, this sort function will be used to pick an alternative reference from the stack. 'None' implies that no attempt will be made to find an alternative reference.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :param cmr_token: EDL Auth Token for authenticated searches, see https://urs.earthdata.nasa.gov/user_tokens
    :param cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider

    :return: ASFSearchResults(dict) of search results
    """
    reference_results = product_search(
        [reference_id],
        host=host,
        cmr_token=cmr_token,
        cmr_provider=cmr_provider)

    try:
        if len(reference_results['features']) <= 0:
            raise ASFSearchError(f'Reference product not found: {reference_id}')
        reference = reference_results['features'][0]
    except KeyError as e:
        raise ASFSearchError(f'Reference product not found: {reference_id}')

    return stack_from_product(reference, host=host, cmr_token=cmr_token, cmr_provider=cmr_provider)


def get_stack_params(reference: ASFProduct) -> dict:

    stack_params = {
        'processingLevel': [reference['properties']['processingLevel']]
    }

    if reference['properties']['platform'] in precalc_platforms:
        if reference['properties']['insarStackId'] not in [None, 'NA', 0, '0']:
            stack_params['insarStackId'] = reference['properties']['insarStackId']
            return stack_params
        else:
            raise ASFBaselineError(f'Requested reference product needs a baseline stack ID but does not have one: {reference["properties"]["fileID"]}')

    # build a stack from scratch if it's a non-precalc dataset with state vectors
    if reference['properties']['platform'] in [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B]:
        stack_params['platform'] = [reference['properties']['platform']]
        stack_params['beamMode'] = [reference['properties']['beamModeType']]
        stack_params['flightDirection'] = [reference['properties']['flightDirection']]
        #stack_params['lookDirection'] = [ref_scene['properties']['lookDirection']]
        stack_params['relativeOrbit'] = [int(reference['properties']['pathNumber'])]  # path
        if reference['properties']['polarization'] in ['HH', 'HH+HV']: stack_params['polarization'] = ['HH','HH+HV']
        elif reference['properties']['polarization'] in ['VV', 'VV+VH']: stack_params['polarization'] = ['VV','VV+VH']
        else: stack_params['polarization'] = [reference['properties']['polarization']]
        ref_centroid = reference.centroid()
        stack_params['intersectsWith'] = f'POINT({ref_centroid[0]} {ref_centroid[1]})'
        return stack_params

    raise ASFBaselineError(f'Reference product is not a pre-calculated baseline dataset, and not a known ephemeris-based dataset: {reference["properties"]["fileID"]}')


def calc_temporal_baselines(reference: ASFProduct, stack: dict) -> None:
    """
    Calculates temporal baselines for a stack of products based on a reference scene and injects those values into the stack.

    :param reference: The reference product from which to calculate temporal baselines.
    :param stack: The stack to operate on.
    :return: None, as the operation occurs in-place on the stack provided.
    """
    pass



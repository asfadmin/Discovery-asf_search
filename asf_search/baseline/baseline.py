from typing import Union, Iterable
import numpy as np
import asf_search


precalc_platforms = [
    asf_search.PLATFORM.ALOS,
    asf_search.PLATFORM.RADARSAT,
    asf_search.PLATFORM.ERS1,
    asf_search.PLATFORM.ERS2,
    asf_search.PLATFORM.JERS]


def stack(
        reference_id: str,
        strategy = None,
        host: str = asf_search.INTERNAL.HOST,
        output: str = 'geojson',
        cmr_token: str = None,
        cmr_provider: str = None) -> dict:
    """
    Builds a baseline stack from a reference scene

    :param reference: Reference scene to base the stack from, and from which to calculate perpendicular/temporal baselines
    :param strategy: If the requested reference can not be used to calculate perpendicular baselines, this sort function will be used to pick an alternative reference from the stack. 'None' implies that no attempt will be made to find an alternative reference.
    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :param output: SearchAPI output format, can be used to alter what metadata is returned and the structure of the results.
    :param cmr_token: EDL Auth Token for authenticated searches, see https://urs.earthdata.nasa.gov/user_tokens
    :param cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider

    :return: Dictionary of search results
    """

    stack_params = get_stack_params(reference_id, host=host, cmr_token=cmr_token, cmr_provider=cmr_provider)
    stack_results = asf_search.search(**stack_params, host=host, cmr_token=cmr_token, cmr_provider=cmr_provider, output=output)
    return stack_results


def get_stack_params(
        reference_id: str,
        host: str = asf_search.INTERNAL.HOST,
        cmr_token: str = None,
        cmr_provider: str = None) -> dict:

    reference_results = asf_search.product_search(
        [reference_id],
        host=host,
        cmr_token=cmr_token,
        cmr_provider=cmr_provider)

    try:
        if len(reference_results['features']) <= 0:
            raise ValueError(f'Reference scene not found: {reference_id}')
        ref_scene = reference_results['features'][0]
    except KeyError as e:
        raise ValueError(f'Error when looking up reference scene: {reference_id}')

    stack_params = {
        'processingLevel': [ref_scene['properties']['processingLevel']]
    }

    if ref_scene['properties']['platform'] in precalc_platforms:
        if ref_scene['properties']['insarGrouping'] not in [None, 'NA', 0, '0']:
            stack_params['insarstackid'] = ref_scene['properties']['insarGrouping']
            return stack_params
        else:
            raise ValueError(f'Requested reference scene needs a baseline stack ID but does not have one: {reference_id}')

    # build a stack from scratch if it's a non-precalc dataset with state vectors
    if ref_scene['properties']['platform'] in [asf_search.PLATFORM.SENTINEL1A, asf_search.PLATFORM.SENTINEL1B]:
        stack_params['platform'] = [ref_scene['properties']['platform']]
        stack_params['beamMode'] = [ref_scene['properties']['beamModeType']]
        stack_params['flightDirection'] = [ref_scene['properties']['flightDirection']]
        #stack_params['lookDirection'] = [ref_scene['properties']['lookDirection']]
        stack_params['relativeOrbit'] = [int(ref_scene['properties']['pathNumber'])]  # path
        if ref_scene['properties']['polarization'] in ['HH', 'HH+HV']: stack_params['polarization'] = ['HH','HH+HV']
        elif ref_scene['properties']['polarization'] in ['VV', 'VV+VH']: stack_params['polarization'] = ['VV','VV+VH']
        else: stack_params['polarization'] = [ref_scene['properties']['polarization']]
        ref_centroid = centroid(ref_scene['geometry']['coordinates'][0]) # centroid of the outer ring
        stack_params['intersectsWith'] = f'POINT({ref_centroid[0]} {ref_centroid[1]})'
    else:
        raise ValueError(f'Reference granule is not a pre-calculated baseline dataset, and not a known ephemeris-based dataset: {reference_id}')

    return stack_params


def centroid(geometry: Iterable) -> (float, float):
    """
    Convenience function to find the centroid of a geometry
    Shamelessly lifted from https://stackoverflow.com/a/23021198 and https://stackoverflow.com/a/57183264
    """
    arr = np.array(geometry)
    length, dim = arr.shape
    return [np.sum(arr[:, i]) / length for i in range(dim)]

from asf_search import ASF_LOGGER

from .validators import (
    parse_string,
    parse_float,
    parse_int,
    parse_wkt,
    parse_date,
    parse_string_list,
    parse_int_list,
    parse_int_or_range_list,
    parse_float_or_range_list,
    parse_cmr_keywords_list,
    parse_session,
    parse_circle,
    parse_linestring,
    parse_point,
    parse_bbox,
)


def validate(key, value):
    if key not in validator_map:
        error_msg = f'Key "{key}" is not a valid search option.'
        # See if they just missed up case sensitivity:
        for valid_key in validator_map:
            if key.lower() == valid_key.lower():
                error_msg += f' (Did you mean "{valid_key}"?)'
                break
        ASF_LOGGER.error(error_msg)
        raise KeyError(error_msg)
    try:
        return validator_map[key](value)
    except ValueError as exc:
        ASF_LOGGER.exception(f'Failed to parse item in ASFSearchOptions: {key=} {value=} {exc=}')
        raise


validator_map = {
    # Search parameters       Parser
    'maxResults': int,
    'absoluteOrbit': parse_int_or_range_list,
    'asfFrame': parse_int_or_range_list,
    'bbox': parse_bbox,
    'beamMode': parse_string_list,
    'beamSwath': parse_string_list,
    'campaign': parse_string,
    'circle': parse_circle,
    'linestring': parse_linestring,
    'point': parse_point,
    'maxDoppler': parse_float,
    'minDoppler': parse_float,
    'maxBaselinePerp': parse_float,
    'minBaselinePerp': parse_float,
    'maxInsarStackSize': parse_int,
    'minInsarStackSize': parse_int,
    'maxFaradayRotation': parse_float,
    'minFaradayRotation': parse_float,
    'flightDirection': parse_string,
    'flightLine': parse_string,
    'frame': parse_int_or_range_list,
    'granule_list': parse_string_list,
    'product_list': parse_string_list,
    'intersectsWith': parse_wkt,
    'lookDirection': parse_string,
    'offNadirAngle': parse_float_or_range_list,
    'platform': parse_string_list,
    'polarization': parse_string_list,
    'processingLevel': parse_string_list,
    'relativeOrbit': parse_int_or_range_list,
    'processingDate': parse_date,
    'start': parse_date,
    'end': parse_date,
    'season': parse_int_list,
    'groupID': parse_string_list,
    'insarStackId': parse_string,
    'instrument': parse_string_list,
    'collections': parse_string_list,
    'shortName': parse_string_list,
    'dataset': parse_string_list,
    'cmr_keywords': parse_cmr_keywords_list,
    # S1 Inteferrogram Filters
    'temporalBaselineDays': parse_string_list,
    # Opera Burst Filters
    'operaBurstID': parse_string_list,
    # SLC Burst Filters
    'absoluteBurstID': parse_int_list,
    'relativeBurstID': parse_int_list,
    'fullBurstID': parse_string_list,
    # nisar paramaters
    'frameCoverage': parse_string,
    'jointObservation': bool,
    'mainBandPolarization': parse_string_list,
    'sideBandPolarization': parse_string_list,
    'rangeBandwidth': parse_string_list,
    # Config parameters       Parser
    'session': parse_session,
    'host': parse_string,
    'provider': parse_string,
    'collectionAlias': bool,
}

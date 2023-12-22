from asf_search import ASF_LOGGER

from .validators import (
    parse_string, parse_float, parse_wkt, parse_date,
    parse_string_iterator, parse_int_iterator, parse_int_or_range_iterator,
    parse_float_or_range_iterator,
    parse_session
)


def validate(key, value):
    if key not in validator_map:
        error_msg = f"Key '{key}' is not a valid search option."
        # See if they just missed up case sensitivity:
        for valid_key in validator_map:
            if key.lower() == valid_key.lower():
                error_msg += f" (Did you mean '{valid_key}'?)"
                break
        ASF_LOGGER.error(error_msg)
        raise KeyError(error_msg)
    try:
        return validator_map[key](value)
    except ValueError as exc:
        ASF_LOGGER.exception(f"Failed to parse item in ASFSearchOptions: {key=} {value=} {exc=}")
        raise

validator_map = {
    # Search parameters       Parser
    'maxResults':             int,
    'absoluteOrbit':          parse_int_or_range_iterator,
    'asfFrame':               parse_int_or_range_iterator,
    'beamMode':               parse_string_iterator,
    'beamSwath':              parse_string_iterator,
    'campaign':               parse_string,
    'maxDoppler':             parse_float,
    'minDoppler':             parse_float,
    'maxFaradayRotation':     parse_float,
    'minFaradayRotation':     parse_float,
    'flightDirection':        parse_string,
    'flightLine':             parse_string,
    'frame':                  parse_int_or_range_iterator,
    'granule_list':           parse_string_iterator,
    'product_list':           parse_string_iterator,
    'intersectsWith':         parse_wkt,
    'lookDirection':          parse_string,
    'offNadirAngle':          parse_float_or_range_iterator,
    'platform':               parse_string_iterator,
    'polarization':           parse_string_iterator,
    'processingLevel':        parse_string_iterator,
    'relativeOrbit':          parse_int_or_range_iterator,
    'processingDate':         parse_date,
    'start':                  parse_date,
    'end':                    parse_date,
    'season':                 parse_int_iterator,
    'groupID':                parse_string_iterator,
    'insarStackId':           parse_string,
    'instrument':             parse_string,
    'collections':            parse_string_iterator,
    'temporalBaselineDays':   parse_string_iterator,
    'operaBurstID':           parse_string_iterator,
    'absoluteBurstID':        parse_int_iterator,
    'relativeBurstID':        parse_int_iterator,
    'fullBurstID':            parse_string_iterator,
    'dataset':                parse_string_iterator,

    # Config parameters       Parser
    'session':                parse_session,
    'host':                   parse_string,
    'provider':               parse_string
}

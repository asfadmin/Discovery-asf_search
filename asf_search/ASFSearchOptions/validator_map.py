
from .validators import (
    parse_int, parse_float, parse_string, parse_wkt, parse_date,
    parse_string_list, parse_int_list, parse_int_or_range_list,
    parse_float_or_range_list,
    parse_coord_string, parse_bbox_string, parse_point_string
)

## Not included in map:
# host
# cmr_token
# cmr_provider

validator_map = {
#   API parameter             Parser
    'maxResults':             parse_int,
    'absoluteOrbit':          parse_int_or_range_list,
    'asfFrame':               parse_int_or_range_list,
    'beamMode':               parse_string_list,
    'collectionName':         parse_string,
    'maxDoppler':             parse_float,
    'minDoppler':             parse_float,
    'maxFaradayRotation':     parse_float,
    'minFaradayRotation':     parse_float,
    'flightDirection':        parse_string,
    'flightLine':             parse_string,
    'frame':                  parse_int_or_range_list,
    'granule_list':           parse_string_list,
    'product_list':           parse_string_list,
    'intersectsWith':         parse_wkt,
    'lookDirection':          parse_string,
    'offNadirAngle':          parse_float_or_range_list,
    'platform':               parse_string_list,
    'polarization':           parse_string_list,
    'processingLevel':        parse_string_list,
    'relativeOrbit':          parse_int_or_range_list,
    'processingDate':         parse_date,
    'start':                  parse_date,
    'end':                    parse_date,
    'season':                 parse_int_list,
    'groupID':                parse_string_list,
    'insarStackId':           parse_string,
    'instrument':             parse_string,
}



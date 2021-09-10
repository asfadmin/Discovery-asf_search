
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
    'maxresults':             parse_int,
    'absoluteorbit':          parse_int_or_range_list,
    'asfframe':               parse_int_or_range_list,
    'beammode':               parse_string_list,
    'collectionname':         parse_string,
    'maxdoppler':             parse_float,
    'mindoppler':             parse_float,
    'maxfaradayrotation':     parse_float,
    'minfaradayrotation':     parse_float,
    'flightdirection':        parse_string,
    'flightline':             parse_string,
    'frame':                  parse_int_or_range_list,
    'granule_list':           parse_string_list,
    'product_list':           parse_string_list,
    'intersectswith':         parse_wkt,
    'lookdirection':          parse_string,
    'offnadirangle':          parse_float_or_range_list,
    'platform':               parse_string_list,
    'polarization':           parse_string_list,
    'processinglevel':        parse_string_list,
    'relativeorbit':          parse_int_or_range_list,
    'processingdate':         parse_date,
    'start':                  parse_date,
    'end':                    parse_date,
    'season':                 parse_int_list,
    'groupid':                parse_string_list,
    'insarstackid':           parse_string,
    'instrument':             parse_string,
}



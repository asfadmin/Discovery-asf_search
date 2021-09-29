
from .validators import (
    parse_string, parse_wkt, parse_date,
    parse_string_list, parse_int_list, parse_int_or_range_list,
    parse_float_or_range_list,
    parse_coord_list, parse_bbox_list, parse_point_list,
    parse_session
)

import dateparser


## Not included in map:
# host
# cmr_token

def validate(key, value):
    if key not in validator_map:
        error_msg = f"Key '{key}' is not a valid search option."
        ## See if they just missed up case sensitivity:
        for valid_key in validator_map:
            if key.lower() == valid_key.lower():
                error_msg += f" (Did you mean '{valid_key}'?)"
                break
        raise KeyError(error_msg)
    return validator_map[key](value)

validator_map = {
#   API parameters            Parser
    'maxResults':             int,
    'absoluteOrbit':          parse_int_or_range_list,
    'asfFrame':               parse_int_or_range_list,
    'beamMode':               parse_string_list,
    'cmr_provider':           parse_string,
    'collectionName':         parse_string,
    'maxDoppler':             float,
    'minDoppler':             float,
    'maxFaradayRotation':     float,
    'minFaradayRotation':     float,
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
#   Internal parameters       Parser
    'asf_session':            parse_session,
}


"""
Key Descriptions:

absoluteOrbit: For ALOS, ERS-1, ERS-2, JERS-1, and RADARSAT-1, Sentinel-1A, Sentinel-1B this value corresponds to the orbit count within the orbit cycle. For UAVSAR it is the Flight ID.
asfFrame: This is primarily an ASF / JAXA frame reference. However, some platforms use other conventions. See ‘frame’ for ESA-centric frame searches.
beamMode: The beam mode used to acquire the data.
collectionName: For UAVSAR and AIRSAR data collections only. Search by general location, site description, or data grouping as supplied by flight agency or project.
maxDoppler: Doppler provides an indication of how much the look direction deviates from the ideal perpendicular flight direction acquisition.
minDoppler: Doppler provides an indication of how much the look direction deviates from the ideal perpendicular flight direction acquisition.
end: End date of data acquisition. Supports timestamps as well as natural language such as "3 weeks ago"
maxFaradayRotation: Rotation of the polarization plane of the radar signal impacts imagery, as HH and HV signals become mixed.
minFaradayRotation: Rotation of the polarization plane of the radar signal impacts imagery, as HH and HV signals become mixed.
flightDirection: Satellite orbit direction during data acquisition
flightLine: Specify a flightline for UAVSAR or AIRSAR.
frame: ESA-referenced frames are offered to give users a universal framing convention. Each ESA frame has a corresponding ASF frame assigned. See also: asfframe
granule_list: List of specific granules. Search results may include several products per granule name.
groupID: Identifier used to find products considered to be of the same scene but having different granule names
insarStackId: Identifier used to find products of the same InSAR stack
instrument: The instrument used to acquire the data. See also: platform
intersectsWith: Search by polygon, linestring, or point defined in 2D Well-Known Text (WKT)
lookDirection: Left or right look direction during data acquisition
offNadirAngle: Off-nadir angles for ALOS PALSAR
platform: Remote sensing platform that acquired the data. Platforms that work together, such as Sentinel-1A/1B and ERS-1/2 have multi-platform aliases available. See also: instrument
polarization: A property of SAR electromagnetic waves that can be used to extract meaningful information about surface properties of the earth.
processingDate: Used to find data that has been processed at ASF since a given time and date. Supports timestamps as well as natural language such as "3 weeks ago"
processingLevel: Level to which the data has been processed
product_list: List of specific products. Guaranteed to be at most one product per product name.
relativeOrbit: Path or track of satellite during data acquisition. For UAVSAR it is the Line ID.
season: Start and end day of year for desired seasonal range. This option is used in conjunction with start/end to specify a seasonal range within an overall date range.
start: Start date of data acquisition. Supports timestamps as well as natural language such as "3 weeks ago"
maxResults: The maximum number of results to be returned by the search

These keys TBD:

host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
cmr_token: EDL authentication token for authenticated searches, see https://urs.earthdata.nasa.gov/user_tokens
cmr_provider: Custom provider name to constrain CMR results to, for more info on how this is used, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-provider
"""

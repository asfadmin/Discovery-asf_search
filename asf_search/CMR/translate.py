from ast import Tuple
from datetime import datetime
from typing import Any, Dict
from asf_search.ASFSearchOptions import ASFSearchOptions, validators
from asf_search.constants import DEFAULT_PROVIDER, CMR_PAGE_SIZE
# from asf_search.search.search import fix_date
import dateparser
from .field_map import field_map

from WKTUtils import RepairWKT, Input

from warnings import warn

def translate_opts(opts: ASFSearchOptions) -> list:
    # Start by just grabbing the searchable parameters
    dict_opts = dict(opts)
    # provider doesn't get copied with the 'dict' cast above
    dict_opts['provider'] = getattr(opts, 'provider', DEFAULT_PROVIDER)
    
    # # CMR requires non-wkt format for shapes
    # # [polygon/linestring/point]: 0, 0, 20, 20, ...
    # if 'intersectsWith' in dict_opts:
    #     shape_type, shape = validators.parse_wkt(dict_opts.pop('intersectsWith')).split(':')
    #     dict_opts[shape_type] = shape

    # Special case to unravel WKT field a little for compatibility
    if dict_opts.get('intersectsWith') is not None:
        repaired_wkt = RepairWKT.repairWKT(dict_opts['intersectsWith'])
        if "errors" in repaired_wkt:
            raise ValueError(f"Error repairing wkt: {repaired_wkt['errors']}")
        for repair in repaired_wkt["repairs"]:
            warn(f"Modified shape: {repair}")
        # DO we want unwrapped here??
        opts.intersectsWith = repaired_wkt["wkt"]["wrapped"]
        cmr_wkt = Input.parse_wkt_util(repaired_wkt["wkt"]["wrapped"])

        (shapeType, shape) = cmr_wkt.split(':')
        del dict_opts['intersectsWith']
        dict_opts[shapeType] = shape


    dict_opts = fix_date(dict_opts)
    dict_opts = fix_platform(dict_opts)
    # convert the above parameters to a list of key/value tuples
    cmr_opts = []
    for (key, val) in dict_opts.items():
        if isinstance(val, list):
            for x in val:
                if key in ['granule_list', 'product_list']:
                    for y in x.split(','):
                        cmr_opts.append((key, y))
                else:
                    cmr_opts.append((key, x))
        else:
            cmr_opts.append((key, val))

    # translate the above tuples to CMR key/values
    for i, opt in enumerate(cmr_opts):
        cmr_opts[i] = field_map[opt[0]]['key'], field_map[opt[0]]['fmt'].format(opt[1])
    
    cmr_opts.append(('page_size', CMR_PAGE_SIZE))

    return cmr_opts


def translate_product(item: dict) -> dict:
    coordinates = item['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']['GPolygons'][0]['Boundary']['Points']
    coordinates = [[c['Longitude'], c['Latitude']] for c in coordinates]
    geometry = {'coordinates': [coordinates], 'type': 'Polygon'}

    umm = item['umm']

    properties = {
        'beamModeType': get(umm, 'AdditionalAttributes', ('Name', 'BEAM_MODE_TYPE'), 'Values', 0),
        'browse': get(umm, 'RelatedUrls', ('Type', 'GET RELATED VISUALIZATION'), 'URL'),
        'bytes': cast(int, try_strip_trailing_zero(get(umm, 'AdditionalAttributes', ('Name', 'BYTES'), 'Values', 0))),
        'centerLat': cast(float, get(umm, 'AdditionalAttributes', ('Name', 'CENTER_LAT'), 'Values', 0)),
        'centerLon': cast(float, get(umm, 'AdditionalAttributes', ('Name', 'CENTER_LON'), 'Values', 0)),
        'faradayRotation': cast(float, get(umm, 'AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0)),
        'fileID': get(umm, 'GranuleUR'),
        'flightDirection': get(umm, 'AdditionalAttributes', ('Name', 'FLIGHT_DIRECTION'), 'Values', 0),
        'groupID': get(umm, 'AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0),
        'granuleType': get(umm, 'AdditionalAttributes', ('Name', 'GRANULE_TYPE'), 'Values', 0),
        'insarStackId': get(umm, 'AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0),
        'md5sum': get(umm, 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0),
        'offNadirAngle': cast(float, get(umm, 'AdditionalAttributes', ('Name', 'OFF_NADIR_ANGLE'), 'Values', 0)),
        'orbit': cast(int, get(umm, 'OrbitCalculatedSpatialDomains', 0, 'OrbitNumber')),
        'pathNumber': cast(int, get(umm, 'AdditionalAttributes', ('Name', 'PATH_NUMBER'), 'Values', 0)),
        'platform': get(umm, 'AdditionalAttributes', ('Name', 'ASF_PLATFORM'), 'Values', 0),
        'pointingAngle': cast(float, get(umm, 'AdditionalAttributes', ('Name', 'POINTING_ANGLE'), 'Values', 0)),
        'polarization': get(umm, 'AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values', 0),
        'processingDate': get(umm, 'DataGranule', 'ProductionDateTime'),
        'processingLevel': get(umm, 'AdditionalAttributes', ('Name', 'PROCESSING_TYPE'), 'Values', 0),
        'sceneName': get(umm, 'DataGranule', 'Identifiers', ('IdentifierType', 'ProducerGranuleId'), 'Identifier'),
        'sensor': get(umm, 'Platforms', 0, 'Instruments', 0, 'ShortName'),
        'startTime': get(umm, 'TemporalExtent', 'RangeDateTime', 'BeginningDateTime'),
        'stopTime': get(umm, 'TemporalExtent', 'RangeDateTime', 'EndingDateTime'),
        'url': get(umm, 'RelatedUrls', ('Type', 'GET DATA'), 'URL')
    }

    stateVectors = {}
    positions = {}
    velocities = {}
    positions['prePosition'], positions['prePositionTime'] = cast(get_state_vector, get(umm, 'AdditionalAttributes', ('Name', 'SV_POSITION_PRE'), 'Values', 0))
    positions['postPosition'], positions['postPositionTime'] = cast(get_state_vector, get(umm, 'AdditionalAttributes', ('Name', 'SV_POSITION_POST'), 'Values', 0))
    velocities['preVelocity'], velocities['preVelocityTime'] = cast(get_state_vector, get(umm, 'AdditionalAttributes', ('Name', 'SV_VELOCITY_PRE'), 'Values', 0))
    velocities['postVelocity'], velocities['postVelocityTime'] = cast(get_state_vector, get(umm, 'AdditionalAttributes', ('Name', 'SV_VELOCITY_POST'), 'Values', 0))
    ascendingNodeTime = get(umm, 'AdditionalAttributes', ('Name', 'ASC_NODE_TIME'), 'Values', 0)


    stateVectors = {
        'positions': positions,
        'velocities': velocities
    }

    insarBaseline = cast(float, get(umm, 'AdditionalAttributes', ('Name', 'INSAR_BASELINE'), 'Values', 0))
    
    baseline = {}
    if None not in stateVectors['positions'].values() and len(stateVectors.items()) > 0:
        baseline['stateVectors'] = stateVectors
        baseline['ascendingNodeTime'] = ascendingNodeTime
    elif insarBaseline is not None:
        baseline['insarBaseline'] = insarBaseline
    else:
        baseline = None


    properties['fileName'] = properties['url'].split('/')[-1]

    asf_frame_platforms = ['Sentinel-1A', 'Sentinel-1B', 'ALOS']
    if properties['platform'] in asf_frame_platforms:
        properties['frameNumber'] = get(umm, 'AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0)
    else:
        properties['frameNumber'] = get(umm, 'AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0)

    return {'geometry': geometry, 'properties': properties, 'type': 'Feature', 'baseline': baseline}


def cast(f, v):
    try:
        return f(v)
    except TypeError:
        return None


def get(item: dict, *args):
    for key in args:
        if isinstance(key, int):
            item = item[key] if key < len(item) else None
        elif isinstance(key, tuple):
            (a, b) = key
            found = False
            for child in item:
                if get(child, a) == b:
                    item = child
                    found = True
                    break
            if not found:
                return None
        else:
            item = item.get(key)
        if item is None:
            return None
    if item in [None, 'NA', 'N/A', '']:
        item = None
    return item

def get_state_vector(state_vector: str):
    if state_vector is None:
        return None, None
    
    return list(map(float, state_vector.split(',')[:3])), state_vector.split(',')[-1]

def try_strip_trailing_zero(value: str):
    if value != None:
        return value.rstrip('.0')
    
    return value

def fix_date(fixed_params: Dict[str, Any]):
    if 'start' in fixed_params or 'end' in fixed_params or 'season' in fixed_params:
        # set default start and end dates if needed, and then make sure they're formatted correctly
        # whether using the default or not
        # set_start = fixed_params.index('start')
        start_s = fixed_params['start'].isoformat() if 'start' in fixed_params else '1978-01-01T00:00:00Z'
        end_s = fixed_params['end'].isoformat() if 'end' in fixed_params else datetime.utcnow().isoformat()

        start = dateparser.parse(start_s, settings={'RETURN_AS_TIMEZONE_AWARE': True})
        end = dateparser.parse(end_s, settings={'RETURN_AS_TIMEZONE_AWARE': True})

        # Check/fix the order of start/end
        if start > end:
            start, end = end, start

        # Final temporal string that will actually be used
        fixed_params['temporal'] = '{0},{1}'.format(
            start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            end.strftime('%Y-%m-%dT%H:%M:%SZ')
        )

        # add the seasonal search if requested now that the regular dates are
        # sorted out
        if 'season' in fixed_params:
            fixed_params['temporal'] += ',{0}'.format(
                ','.join(str(x) for x in fixed_params['season'])
            )

        # And a little cleanup
        fixed_params.pop('start', None)
        fixed_params.pop('end', None)
        fixed_params.pop('season', None)
        
    return fixed_params

def fix_platform(fixed_params: Dict[str, Any]):
    if 'platform' not in fixed_params:
        # Nothing to do
        return fixed_params

    # If it's a single plat str, make it a list of that plat:
    if not isinstance(fixed_params["platform"], list):
        fixed_params["platform"] = [ fixed_params["platform"] ]

    plat_aliases = {
        # Groups:
        'S1': ['SENTINEL-1A', 'SENTINEL-1B'],
        'SENTINEL-1': ['SENTINEL-1A', 'SENTINEL-1B'],
        'SENTINEL': ['SENTINEL-1A', 'SENTINEL-1B'],
        'ERS': ['ERS-1', 'ERS-2'],
        'SIR-C': ['STS-59', 'STS-68'],
        # Singles / Aliases:
        'R1': ['RADARSAT-1'],
        'E1': ['ERS-1'],
        'E2': ['ERS-2'],
        'J1': ['JERS-1'],
        'A3': ['ALOS'],
        'AS': ['DC-8'],
        'AIRSAR': ['DC-8'],
        'SS': ['SEASAT 1'],
        'SEASAT': ['SEASAT 1'],
        'SA': ['SENTINEL-1A'],
        'SB': ['SENTINEL-1B'],
        'SP': ['SMAP'],
        'UA': ['G-III'],
        'UAVSAR': ['G-III'],
    }

    # Legacy API allowed a few synonyms. If they're using one,
    # translate it. Also handle airsar/seasat/uavsar platform
    # conversion
    platform_list = []
    for plat in fixed_params["platform"]:
        if plat.upper() in plat_aliases:
            platform_list.extend(plat_aliases[plat.upper()])
        else:
            platform_list.append(plat)

    fixed_params["platform"] = platform_list
    return fixed_params
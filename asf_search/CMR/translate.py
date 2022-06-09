from ast import Tuple
from datetime import datetime
from typing import Any, Dict
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.constants import DEFAULT_PROVIDER
# from asf_search.search.search import fix_date
import dateparser
from .field_map import field_map


def translate_opts(opts: ASFSearchOptions) -> list:
    # Start by just grabbing the searchable parameters
    dict_opts = dict(opts)
    # provider doesn't get copied with the 'dict' cast above
    dict_opts['provider'] = getattr(opts, 'provider', DEFAULT_PROVIDER)

    dict_opts = fix_date(dict_opts)
    # convert the above parameters to a list of key/value tuples
    cmr_opts = []
    for (key, val) in dict_opts.items():
        if key == 'intersectsWith':
            cmr_opts.append((val.split(':')[0], val.split(':')[1]))
        elif isinstance(val, list):
            for x in val:
                cmr_opts.append((key, x))
        else:
            cmr_opts.append((key, val))

        # cmr_opts.append((wkt.split(':')[0], wkt.split(':')[1]))
        
    # translate the above tuples to CMR key/values
    for i, opt in enumerate(cmr_opts):
        cmr_opts[i] = field_map[opt[0]]['key'], field_map[opt[0]]['fmt'].format(opt[1])

    return cmr_opts


def translate_product(item: dict) -> dict:
    coordinates = item['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']['GPolygons'][0]['Boundary']['Points']
    coordinates = [[c['Longitude'], c['Latitude']] for c in coordinates]
    geometry = {'coordinates': [coordinates], 'type': 'Polygon'}

    umm = item['umm']

    properties = {
        'beamModeType': get(umm, 'AdditionalAttributes', ('Name', 'BEAM_MODE_TYPE'), 'Values', 0),
        'browse': get(umm, 'RelatedUrls', ('Type', 'GET RELATED VISUALIZATION'), 'URL'),
        'bytes': cast(int, get(umm, 'AdditionalAttributes', ('Name', 'BYTES'), 'Values', 0).rstrip('.0')),
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
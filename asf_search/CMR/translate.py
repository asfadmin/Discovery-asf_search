from datetime import datetime
from typing import Any, Dict, List
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.constants import CMR_PAGE_SIZE
import re
from shapely import wkt
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from .field_map import field_map

import logging


def translate_opts(opts: ASFSearchOptions) -> list:
    # Need to add params which ASFSearchOptions cant support (like temporal),
    # so use a dict to avoid the validate_params logic:
    dict_opts = dict(opts)

    # Escape commas for each key in the list.
    # intersectsWith, temporal, and other keys you don't want to escape, so keep whitelist instead
    for escape_commas in ["campaign"]:
        if escape_commas in dict_opts:
            dict_opts[escape_commas] = dict_opts[escape_commas].replace(",", "\,")

    # Special case to unravel WKT field a little for compatibility
    if "intersectsWith" in dict_opts:
        shape = wkt.loads(dict_opts.pop('intersectsWith', None))

        # If a wide rectangle is provided, make sure to use the bounding box
        # instead of the wkt for better responses from CMR
        # This will provide better results with AOI's near poles
        if should_use_bbox(shape):
            bounds = shape.boundary.bounds
            if bounds[0] > 180 or bounds[2] > 180:
                bounds = [(x + 180) % 360 - 180 if idx % 2 == 0 and abs(x) > 180 else x for idx, x in enumerate(bounds)]

            bottom_left = [str(coord) for coord in bounds[:2]]
            top_right = [str(coord) for coord in bounds[2:]]

            bbox = ','.join([*bottom_left, *top_right])
            dict_opts['bbox'] = bbox
        else:
            (shapeType, shape) = wkt_to_cmr_shape(shape).split(':')
            dict_opts[shapeType] = shape

    # If you need to use the temporal key:
    if any(key in dict_opts for key in ['start', 'end', 'season']):
        dict_opts = fix_date(dict_opts)

    # convert the above parameters to a list of key/value tuples
    cmr_opts = []
    for (key, val) in dict_opts.items():
        # If it's "session" or something else CMR doesn't accept, don't send it:
        if key not in field_map:
            continue
        if isinstance(val, list):
            for x in val:
                if key in ['granule_list', 'product_list']:
                    for y in x.split(','):
                        cmr_opts.append((key, y))
                else:
                    if isinstance(x, tuple):
                        cmr_opts.append((key, ','.join([str(t) for t in x])))                    
                    else:
                        cmr_opts.append((key, x))
        else:
            cmr_opts.append((key, val))
    # translate the above tuples to CMR key/values
    for i, opt in enumerate(cmr_opts):
        cmr_opts[i] = field_map[opt[0]]['key'], field_map[opt[0]]['fmt'].format(opt[1])

    if should_use_asf_frame(cmr_opts):
            cmr_opts = use_asf_frame(cmr_opts)

    additional_keys = [
        ('page_size', CMR_PAGE_SIZE),
        ('options[temporal][and]', 'true'), 
        ('sort_key[]', '-end_date'), 
        ('sort_key[]', 'granule_ur'), 
        ('options[platform][ignore_case]', 'true'),
        ('provider', opts.provider),
    ]
    
    cmr_opts.extend(additional_keys)

    return cmr_opts


def should_use_asf_frame(cmr_opts):
    asf_frame_platforms = ['SENTINEL-1A', 'SENTINEL-1B', 'ALOS']

    return any([
        p[0] == 'platform[]' and p[1].upper() in asf_frame_platforms
        for p in cmr_opts
    ])


def use_asf_frame(cmr_opts):
    """
    Sentinel/ALOS: always use asf frame instead of esa frame

    Platform-specific hack
    We do them at the subquery level in case the main query crosses
    platforms that don't suffer these issue.
    """

    for n, p in enumerate(cmr_opts):
        if not isinstance(p[1], str):
            continue

        m = re.search(r'CENTER_ESA_FRAME', p[1])
        if m is None:
            continue

        logging.debug(
            'Sentinel/ALOS subquery, using ASF frame instead of ESA frame'
        )

        cmr_opts[n] = (
            p[0],
            p[1].replace(',CENTER_ESA_FRAME,', ',FRAME_NUMBER,')
        )
    
    return cmr_opts


def translate_product(item: dict) -> dict:
    try:
        coordinates = item['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']['GPolygons'][0]['Boundary']['Points']
        coordinates = [[c['Longitude'], c['Latitude']] for c in coordinates]
        geometry = {'coordinates': [coordinates], 'type': 'Polygon'}
    except KeyError as e:
        geometry = {'coordinates': None, 'type': 'Polygon'}

    umm = item.get('umm')

    properties = {
        'beamModeType': get(umm, 'AdditionalAttributes', ('Name', 'BEAM_MODE_TYPE'), 'Values', 0),
        'browse': get(umm, 'RelatedUrls', ('Type', [('GET RELATED VISUALIZATION', 'URL')])),
        'bytes': cast(int, try_round_float(get(umm, 'AdditionalAttributes', ('Name', 'BYTES'), 'Values', 0))),
        'centerLat': cast(float, get(umm, 'AdditionalAttributes', ('Name', 'CENTER_LAT'), 'Values', 0)),
        'centerLon': cast(float, get(umm, 'AdditionalAttributes', ('Name', 'CENTER_LON'), 'Values', 0)),
        'faradayRotation': cast(float, get(umm, 'AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0)),
        'fileID': get(umm, 'GranuleUR'),
        'flightDirection': get(umm, 'AdditionalAttributes', ('Name', 'ASCENDING_DESCENDING'), 'Values', 0),
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
        'url': get(umm, 'RelatedUrls', ('Type', 'GET DATA'), 'URL'),
        'pgeVersion': get(umm, 'PGEVersionClass', 'PGEVersion')
    }
    
    if properties['beamModeType'] is None:
        properties['beamModeType'] = get(umm, 'AdditionalAttributes', ('Name', 'BEAM_MODE'), 'Values', 0)

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

    if properties['url'] is not None:
        properties['fileName'] = properties['url'].split('/')[-1]
    else:
        properties['fileName'] = None

    if properties['platform'] is None:
        properties['platform'] = get(umm, 'Platforms', 0, 'ShortName')

    asf_frame_platforms = ['Sentinel-1A', 'Sentinel-1B', 'ALOS', 'SENTINEL-1A', 'SENTINEL-1B']
    if properties['platform'] in asf_frame_platforms:
        properties['frameNumber'] = cast(int, get(umm, 'AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0))
    else:
        properties['frameNumber'] = cast(int, get(umm, 'AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0))

    if properties['processingLevel'] == 'BURST':
        burst = {
            'absoluteBurstID': cast(int, get(umm, 'AdditionalAttributes', ('Name', 'BURST_ID_ABSOLUTE'), 'Values', 0)),
            'relativeBurstID': cast(int, get(umm, 'AdditionalAttributes', ('Name', 'BURST_ID_RELATIVE'), 'Values', 0)),
            'fullBurstID': get(umm, 'AdditionalAttributes', ('Name', 'BURST_ID_FULL'), 'Values', 0),
            'burstIndex': cast(int, get(umm, 'AdditionalAttributes', ('Name', 'BURST_INDEX'), 'Values', 0)),
            'samplesPerBurst': cast(int, get(umm, 'AdditionalAttributes', ('Name', 'SAMPLES_PER_BURST'), 'Values', 0)),
            'subswath': get(umm, 'AdditionalAttributes', ('Name', 'SUBSWATH_NAME'), 'Values', 0),
            'azimuthTime': get(umm, 'AdditionalAttributes', ('Name', 'AZIMUTH_TIME'), 'Values', 0),
            'azimuthAnxTime': get(umm, 'AdditionalAttributes', ('Name', 'AZIMUTH_ANX_TIME'), 'Values', 0),
        }
        properties['burst'] = burst
        properties['sceneName'] = properties['fileID']
        properties['bytes'] = cast(int, get(umm, 'AdditionalAttributes', ('Name', 'BYTE_LENGTH'),  'Values', 0))

        urls = get(umm, 'RelatedUrls', ('Type', [('USE SERVICE API', 'URL')]), 0)
        if urls is not None:
            properties['url'] = urls[0]
            properties['fileName'] = properties['fileID'] + '.' + urls[0].split('.')[-1]

    return {'geometry': geometry, 'properties': properties, 'type': 'Feature', 'baseline': baseline}

def get_additional_fields(umm, *field_path):
    return get(umm, *field_path)

def cast(f, v):
    try:
        return f(v)
    except TypeError:
        return None


def get(item: dict, *args):
    if item is None:
        return None
    for key in args:
        if isinstance(key, int):
            item = item[key] if key < len(item) else None
        elif isinstance(key, tuple):
            (a, b) = key
            if isinstance(b, List):
                output = []
                b = b[0]
                for child in item:
                    if get(child, key[0]) == b[0]:
                        output.append(get(child, b[1]))
                if len(output):
                    return output

                return None

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


# some products don't have integer values in BYTES fields, round to nearest int
def try_round_float(value: str):
    if value is not None:
        value = float(value)
        return round(value)
    
    return value


def fix_date(fixed_params: Dict[str, Any]):
    if 'start' in fixed_params or 'end' in fixed_params or 'season' in fixed_params:
        fixed_params["start"] = fixed_params["start"] if "start" in fixed_params else "1978-01-01T00:00:00Z"
        fixed_params["end"] = fixed_params["end"] if "end" in fixed_params else datetime.utcnow().isoformat()
        fixed_params["season"] = ','.join(str(x) for x in fixed_params['season']) if "season" in fixed_params else ""

        fixed_params['temporal'] = f'{fixed_params["start"]},{fixed_params["end"]},{fixed_params["season"]}'

        # And a little cleanup
        fixed_params.pop('start', None)
        fixed_params.pop('end', None)
        fixed_params.pop('season', None)
        
    return fixed_params


def should_use_bbox(shape: BaseGeometry):
    """
    If the passed shape is a polygon, and if that polygon
    is equivalent to it's bounding box (if it's a rectangle),
    we should use the bounding box to search instead
    """
    if isinstance(shape, Polygon):
        coords = [
            [shape.bounds[0], shape.bounds[1]], 
            [shape.bounds[2], shape.bounds[1]],
            [shape.bounds[2], shape.bounds[3]],
            [shape.bounds[0], shape.bounds[3]],
        ]
        return shape.equals(Polygon(shell=coords))
    
    return False


def wkt_to_cmr_shape(shape: BaseGeometry):
    # take note of the WKT type
    if shape.geom_type not in ["Point","LineString", "Polygon"]:
        raise ValueError('Unsupported WKT: {0}.'.format(shape.wkt))
    
    if shape.geom_type == "Polygon":
        coords = shape.exterior.coords
    else: # type == Point | Linestring
        coords = shape.coords
    # Turn [[x,y],[x,y]] into [x,y,x,y]:
    lon_lat_sequence = []
    for lon_lat in coords: lon_lat_sequence.extend(lon_lat)
    # Turn any "6e8" to a literal number. (As a sting):
    coords = ['{:.16f}'.format(float(cord)) for cord in lon_lat_sequence]
    return '{0}:{1}'.format(shape.geom_type.lower(), ','.join(coords))

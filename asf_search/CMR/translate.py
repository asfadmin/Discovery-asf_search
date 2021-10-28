from asf_search.ASFSearchOptions import ASFSearchOptions

from .field_map import field_map


def translate_opts(opts: ASFSearchOptions) -> list:
    # Start by just grabbing the searchable parameters
    dict_opts = dict(opts)

    # convert the above parameters to a list of key/value tuples
    cmr_opts = []
    for (key, val) in dict_opts.items():
        if isinstance(val, list):
            for x in val:
                cmr_opts.append((key, x))
        else:
            cmr_opts.append((key, val))

    # translate the above tuples to CMR key/values
    for i, opt in enumerate(cmr_opts):
        cmr_opts[i] = field_map[opt[0]]['key'], field_map[opt[0]]['fmt'].format(opt[1])

    return cmr_opts


def translate_product(item: dict) -> dict:
    coords = item['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']['GPolygons'][0]['Boundary']['Points']
    coords = [[c['Longitude'], c['Latitude']] for c in coords]
    g = {'coordinates': [coords], 'type': 'Polygon'}

    umm = item['umm']

    p = {}
    p['beamModeType'] = get(umm, 'AdditionalAttributes', ('Name', 'BEAM_MODE_TYPE'), 'Values', 0)
    p['browse'] = get(umm, 'RelatedUrls', ('Type', 'GET RELATED VISUALIZATION'), 'URL')
    p['bytes'] = cast(int, get(umm, 'AdditionalAttributes', ('Name', 'BYTES'), 'Values', 0))
    p['centerLat'] = cast(float, get(umm, 'AdditionalAttributes', ('Name', 'CENTER_LAT'), 'Values', 0))
    p['centerLon'] = cast(float, get(umm, 'AdditionalAttributes', ('Name', 'CENTER_LON'), 'Values', 0))
    p['faradayRotation'] = cast(float, get(umm, 'AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0))
    p['fileID'] = get(umm, 'GranuleUR')
    p['flightDirection'] = get(umm, 'AdditionalAttributes', ('Name', 'FLIGHT_DIRECTION'), 'Values', 0)
    p['groupID'] = get(umm, 'AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0)
    p['granuleType'] = get(umm, 'AdditionalAttributes', ('Name', 'GRANULE_TYPE'), 'Values', 0)
    p['insarStackId'] = get(umm, 'AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0)
    p['md5sum'] = get(umm, 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0)
    p['offNadirAngle'] = cast(float, get(umm, 'AdditionalAttributes', ('Name', 'OFF_NADIR_ANGLE'), 'Values', 0))
    p['orbit'] = cast(int, get(umm, 'OrbitCalculatedSpatialDomains', 0, 'OrbitNumber'))
    p['pathNumber'] = cast(int, get(umm, 'AdditionalAttributes', ('Name', 'PATH_NUMBER'), 'Values', 0))
    p['platform'] = get(umm, 'AdditionalAttributes', ('Name', 'ASF_PLATFORM'), 'Values', 0)
    p['pointingAngle'] = cast(float, get(umm, 'AdditionalAttributes', ('Name', 'POINTING_ANGLE'), 'Values', 0))
    p['polarization'] = get(umm, 'AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values', 0)
    p['processingDate'] = get(umm, 'DataGranule', 'ProductionDateTime')
    p['processingLevel'] = get(umm, 'AdditionalAttributes', ('Name', 'PROCESSING_TYPE'), 'Values', 0)
    p['sceneName'] = get(umm, 'DataGranule', 'Identifiers', ('IdentifierType', 'ProducerGranuleId'), 'Identifier')
    p['sensor'] = get(umm, 'Platforms', 0, 'Instruments', 0, 'ShortName')
    p['startTime'] = get(umm, 'TemporalExtent', 'RangeDateTime', 'BeginningDateTime')
    p['stopTime'] = get(umm, 'TemporalExtent', 'RangeDateTime', 'EndingDateTime')
    p['url'] = get(umm, 'RelatedUrls', ('Type', 'GET DATA'), 'URL')

    p['fileName'] = p['url'].split('/')[-1]

    asf_frame_platforms = ['Sentinel-1A', 'Sentinel-1B', 'ALOS']
    if p['platform'] in asf_frame_platforms:
        p['frameNumber'] = get(umm, 'AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0)
    else:
        p['frameNumber'] = get(umm, 'AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0)

    return {'geometry': g, 'properties': p, 'type': 'Feature'}


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

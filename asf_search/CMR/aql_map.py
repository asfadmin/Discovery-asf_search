from datetime import datetime

# use for CMR "additional attribute" fields
def additional_attribute_to_aql_field(param, attribute_name: str) -> str:
    if not type(param) is list:
        param = [param]

    values = ''.join(list(map(lambda p: '<value>{0}</value>'.format(p), param)))
    
    if len(param) > 1:
        values = f'<list>{values}</list>'

    return f'<additionalAttribute><additionalAttributeName>{attribute_name.upper()}</additionalAttributeName><additionalAttributeValue>' + values + '</additionalAttributeValue></additionalAttribute>'

def cmr_format_to_spatial(val, param: str):
    spatial = '<spatial>{0}</spatial>'
    if param == 'point':
        return spatial.format(to_IIMSPoint(val))
    elif param == 'polygon':
        return spatial.format(to_IIMSPolygon(val))
    elif param == 'bounding_box':
        return spatial.format(to_IIMSBox(val))
    elif param == 'line':
        return spatial.format(to_IIMSLine(val))

def to_IIMSPoint(val: str):
    lon, lat = val.split(',')
    return f'<IIMSPoint lat=\"{lat}\" long=\"{lon}\"></IIMSPoint>'

def to_IIMSPoints(val: str):
    coords = val.split(',')
    points_iter = iter(coords)
    
    points = []
    
    # iterated coordinates by two (long, lat)
    for x, y in zip(points_iter, points_iter):
        points.append(x + ',' + y)
    
    output = ''.join([to_IIMSPoint(point) for point in points])

    print(points)
    
    return output

def to_IIMSLine(val: str):
    return '<IIMSLine>' + to_IIMSPoints(val) + '</IIMSLine>'
    
def to_IIMSPolygon(val: str):
    return '<IIMSPolygon><IIMSLRing>' + to_IIMSPoints(val) + '</IIMSLRing></IIMSPolygon>'

def to_IIMSBox(val: str):
    return '<IIMSBox>' + to_IIMSPoints(val) + '</IIMSBox>'

def to_temporal(val, key):
    temporal_vals = val.split(',')
    start_date, end_date, season_range = (temporal_vals[0], temporal_vals[1], temporal_vals[2:])
    
    start_year, start_month, start_day = start_date.split('-')[0:3]
    start_day = start_day.split('T')[0]
    
    end_year, end_month, end_day = end_date.split('-')[0:3]
    end_day = end_day.split('T')[0]
    
    season = ''
    if len(season_range) > 1:
        season_start, season_end = season_range
        season = f'<startDay value=\'{season_start}\'></startDay><endDay value=\'{season_end}\'></endDay>'
    
    start = to_date_aql_field(start_year, start_month, start_day, 'startDate')
    end = to_date_aql_field(end_year, end_month, end_day, 'stopDate')
    return f'<{key}>{start}{end}{season}</{key}>'

def to_date_aql_field(year, month, day, dateName):
    return f'<{dateName}><Date YYYY=\"{year}\" MM=\"{month}\" DD=\"{day}\"></Date></{dateName}>'

def default_enddate(val: datetime, key):
    start_year = val.year
    start_month = val.month
    start_day = val.day
    return f'<{key}><dateRange>' + to_date_aql_field(start_year, start_month, start_day, 'startDate') + f'</dateRange></{key}>'


def to_defined_aql_field(param, key, operator=None):
    # for built-in CMR AQL fields 
    if not type(param) is list:
        param = [param]
    values = ''.join(list(map(lambda p: '<value>{0}</value>'.format(p), param)))

    if len(param) > 1:
        return f'<{key}' + ((f' operator=' + f'\"{operator}\"') if operator else '') + '><list>' + values + f'</list></{key}>'
    else:
        return f'<{key}>' + values + f'</{key}>'

def to_range_aql_field(param, key):
    lower = param[0]
    upper = ''

    if len(param) > 1:
        upper = f"upper='{param[1]}'"
        
    param_range = f"<{key}><range lower='{lower}' {upper}></range></{key}>"

    return param_range

def to_platform_field(val, key):
    return to_defined_aql_field(val, key, 'OR')

# CMR DEFINED AQL ATTRIBUTES
cmr_attributes_map = {
    'absoluteOrbit':        {'aql_key': 'orbitNumber',              'conv': to_range_aql_field},
    'granule_list':         {'aql_key': 'ProducerGranuleID',        'conv': to_defined_aql_field},
    'instrument':           {'aql_key': 'instrumentShortName',      'conv': to_defined_aql_field},
    'product_list':         {'aql_key': 'GranuleUR',                'conv': to_defined_aql_field},
    'linestring':           {'aql_key': 'line',                     'conv': cmr_format_to_spatial},
    'point':                {'aql_key': 'point',                    'conv': cmr_format_to_spatial},
    'polygon':              {'aql_key': 'polygon',                  'conv': cmr_format_to_spatial},
    'bbox':                 {'aql_key': 'bounding_box',             'conv': cmr_format_to_spatial},
    'temporal':             {'aql_key': 'temporal',                 'conv': to_temporal},
    'processingDate':       {'aql_key': 'ECHOLastUpdate',           'conv': default_enddate},
    'platform':             {'aql_key': 'sourceName',               'conv': to_platform_field},
    # 'provider':             {'key': 'provider',                'fmt': '{0}'},
}

# ADDITIONAL ATTRIBUTES
additional_attributes_map = {
    'asfFrame':             {'aql_key': 'FRAME_NUMBER',             'conv': additional_attribute_to_aql_field},
    'asfPlatform':          {'aql_key': 'ASF_PLATFORM',             'conv': additional_attribute_to_aql_field},
    'maxBaselinePerp':      {'aql_key': 'INSAR_BASELINE',           'conv': additional_attribute_to_aql_field},
    'minBaselinePerp':      {'aql_key': 'INSAR_BASELINE',           'conv': additional_attribute_to_aql_field},
    'beamMode':             {'aql_key': 'BEAM_MODE',                'conv': additional_attribute_to_aql_field},
    'beamSwath':            {'aql_key': 'BEAM_MODE_TYPE',           'conv': additional_attribute_to_aql_field},
    'campaign':             {'aql_key': 'MISSION_NAME',             'conv': additional_attribute_to_aql_field},
    'maxDoppler':           {'aql_key': 'DOPPLER',                  'conv': additional_attribute_to_aql_field},
    'minDoppler':           {'aql_key': 'DOPPLER',                  'conv': additional_attribute_to_aql_field},
    'maxFaradayRotation':   {'aql_key': 'FARADAY_ROTATION',         'conv': additional_attribute_to_aql_field},
    'minFaradayRotation':   {'aql_key': 'FARADAY_ROTATION',         'conv': additional_attribute_to_aql_field},
    'flightDirection':      {'aql_key': 'ASCENDING_DESCENDING',     'conv': additional_attribute_to_aql_field},
    'flightLine':           {'aql_key': 'FLIGHT_LINE',              'conv': additional_attribute_to_aql_field},
    'frame':                {'aql_key': 'CENTER_ESA_FRAME',         'conv': additional_attribute_to_aql_field},
    'groupID':              {'aql_key': 'GROUP_ID',                 'conv': additional_attribute_to_aql_field},
    'insarStackId':         {'aql_key': 'INSAR_STACK_ID',           'conv': additional_attribute_to_aql_field},
    'lookDirection':        {'aql_key': 'LOOK_DIRECTION',           'conv': additional_attribute_to_aql_field},
    'maxInsarStackSize':    {'aql_key': 'INSAR_STACK_SIZE',         'conv': additional_attribute_to_aql_field},
    'minInsarStackSize':    {'aql_key': 'INSAR_STACK_SIZE',         'conv': additional_attribute_to_aql_field},
    'offNadirAngle':        {'aql_key': 'OFF_NADIR_ANGLE',          'conv': additional_attribute_to_aql_field},
    'polarization':         {'aql_key': 'POLARIZATION',             'conv': additional_attribute_to_aql_field},
    'processingLevel':      {'aql_key': 'PROCESSING_TYPE',          'conv': additional_attribute_to_aql_field},
    'relativeOrbit':        {'aql_key': 'PATH_NUMBER',              'conv': additional_attribute_to_aql_field},
}
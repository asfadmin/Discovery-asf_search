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
    if param == 'point':
        return '<granuleCondition><spatial>' + to_iimspoint(val) + '</spatial></granuleCondition>'
    elif param == 'polygon':
        return to_iimspolygon(val)
    elif param == 'bounding_box':
        return to_iimsbox(val)
    elif param == 'line':
        return '<granuleCondition><spatial><IIMSLine>' + to_iimsline(val) + '</IIMSLine></spatial></granuleCondition>'

def to_iimspoint(val: str):
    long, lat  = val.split(',')
    return f'<IIMSPoint lat=\"{lat}\" long=\"{long}\"></IIMSPoint>'

def to_iimsline(val: str):
    coords = val.split(',')
    points_iter = iter(coords)
    
    points = []
    for x, y in zip(points_iter, points_iter):
        points.append(x + ',' + y)
    
    output = ''
    for point in points:
        output += to_iimspoint(point)
    print(points)
    
    return output

def to_iimspolygon(val: str):
    return '<granuleCondition><spatial><IIMSPolygon><IIMSLRing>' + to_iimsline(val) + '</IIMSLRing></IIMSPolygon></spatial></granuleCondition>'

def to_iimsbox(val: str):
    return '<granuleCondition><spatial><IIMSBox>' + to_iimsline(val) + '</IIMSBox></spatial></granuleCondition>'

def to_temporal(val, key):
    temporal_vals = val.split(',')
    startDate, endDate, season_range = (temporal_vals[0], temporal_vals[1], temporal_vals[2:])
    
    startYear, startMonth, startDay = startDate.split('-')[0:3]
    startDay = startDay.split('T')[0]
    
    endYear, endMonth, endDay = endDate.split('-')[0:3]
    endDay = endDay.split('T')[0]
    
    season = ''
    if len(season_range) > 1:
        season_start, season_end = season_range
        season = f'<startDay value=\'{season_start}\'></startDay><endDay value=\'{season_end}\'></endDay>'
    
    start = to_date_aql_field(startYear, startMonth, startDay, 'startDate')
    end = to_date_aql_field(endYear, endMonth, endDay, 'stopDate')
    return f'<granuleCondition><{key}>{start}{end}{season}</{key}></granuleCondition>'

def to_date_aql_field(year, month, day, dateName):
    return f'<{dateName}><Date YYYY=\"{year}\" MM=\"{month}\" DD=\"{day}\"></Date></{dateName}>'

def default_enddate(val: datetime, key):
    startyear  = val.year
    startMonth = val.month
    startDay = val.day
    return f'<granuleCondition><{key}><dateRange>' + to_date_aql_field(startyear, startMonth, startDay, 'startDate') + f'</dateRange></{key}></granuleCondition>'


def to_defined_aql_field(param, key, operator=None):
    # for built-in CMR AQL fields 
    if not type(param) is list:
        param = [param]
    values = ''.join(list(map(lambda p: '<value>{0}</value>'.format(p), param)))

    if len(param) > 1:
        return f'<granuleCondition><{key}' + ((f' operator=' + f'\"{operator}\"') if operator else '') + '><list>'  + values + f'</list></{key}></granuleCondition>'
    else:
        return f'<granuleCondition><{key}>'  + values + f'</{key}></granuleCondition>'

def to_range_aql_field(param, key):
    lower = param[0]
    if len(param) > 1:
        upper = f"upper='{param[1]}'"
    else:
        upper = ''
    param_range = f"<granuleCondition><{key}><range lower='{lower}' {upper}></range></{key}></granuleCondition>"

    return param_range

def to_platform_field(val, key):
    return to_defined_aql_field(val, key, 'OR')

# CMR DEFINED AQL ATTRIBUTES
cmr_attributes_map = {
    'absoluteOrbit':        {'key': 'orbitNumber',              'conv': to_range_aql_field},
    'granule_list':         {'key': 'ProducerGranuleID',        'conv': to_defined_aql_field},
    'instrument':           {'key': 'instrumentShortName',      'conv': to_defined_aql_field},
    'product_list':         {'key': 'GranuleUR',                'conv': to_defined_aql_field},
    'linestring':           {'key': 'line',                     'conv': cmr_format_to_spatial},
    'point':                {'key': 'point',                    'conv': cmr_format_to_spatial},
    'polygon':              {'key': 'polygon',                  'conv': cmr_format_to_spatial},
    'bbox':                 {'key': 'bounding_box',             'conv': cmr_format_to_spatial},
    'temporal':             {'key': 'temporal',                 'conv': to_temporal},
    'processingDate':       {'key': 'ECHOLastUpdate',           'conv': default_enddate},
    'platform':             {'key': 'sourceName',               'conv': to_platform_field},
    # 'provider':             {'key': 'provider',                'fmt': '{0}'},
}

# ADDITIONAL ATTRIBUTES
additional_attributes_map = {
    'asfFrame':             {'key': 'FRAME_NUMBER',             'conv': additional_attribute_to_aql_field},
    'asfPlatform':          {'key': 'ASF_PLATFORM',             'conv': additional_attribute_to_aql_field},
    'maxBaselinePerp':      {'key': 'INSAR_BASELINE',           'conv': additional_attribute_to_aql_field},
    'minBaselinePerp':      {'key': 'INSAR_BASELINE',           'conv': additional_attribute_to_aql_field},
    'beamMode':             {'key': 'BEAM_MODE',                'conv': additional_attribute_to_aql_field},
    'beamSwath':            {'key': 'BEAM_MODE_TYPE',           'conv': additional_attribute_to_aql_field},
    'campaign':             {'key': 'MISSION_NAME',             'conv': additional_attribute_to_aql_field},
    'maxDoppler':           {'key': 'DOPPLER',                  'conv': additional_attribute_to_aql_field},
    'minDoppler':           {'key': 'DOPPLER',                  'conv': additional_attribute_to_aql_field},
    'maxFaradayRotation':   {'key': 'FARADAY_ROTATION',         'conv': additional_attribute_to_aql_field},
    'minFaradayRotation':   {'key': 'FARADAY_ROTATION',         'conv': additional_attribute_to_aql_field},
    'flightDirection':      {'key': 'ASCENDING_DESCENDING',     'conv': additional_attribute_to_aql_field},
    'flightLine':           {'key': 'FLIGHT_LINE',              'conv': additional_attribute_to_aql_field},
    'frame':                {'key': 'CENTER_ESA_FRAME',         'conv': additional_attribute_to_aql_field},
    'groupID':              {'key': 'GROUP_ID',                 'conv': additional_attribute_to_aql_field},
    'insarStackId':         {'key': 'INSAR_STACK_ID',           'conv': additional_attribute_to_aql_field},
    'lookDirection':        {'key': 'LOOK_DIRECTION',           'conv': additional_attribute_to_aql_field},
    'maxInsarStackSize':    {'key': 'INSAR_STACK_SIZE',         'conv': additional_attribute_to_aql_field},
    'minInsarStackSize':    {'key': 'INSAR_STACK_SIZE',         'conv': additional_attribute_to_aql_field},
    'offNadirAngle':        {'key': 'OFF_NADIR_ANGLE',          'conv': additional_attribute_to_aql_field},
    'polarization':         {'key': 'POLARIZATION',             'conv': additional_attribute_to_aql_field},
    'processingLevel':      {'key': 'PROCESSING_TYPE',          'conv': additional_attribute_to_aql_field},
    'relativeOrbit':        {'key': 'PATH_NUMBER',              'conv': additional_attribute_to_aql_field},
}
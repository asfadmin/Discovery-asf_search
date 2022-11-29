from datetime import datetime

def to_aql_attribute_field(param, attribute_name: str):
    if not type(param) is list:
        param = [param]
    # If the attribute is an "additional" attribute, use this format
    values = ''.join(list(map(lambda p: '<value>{0}</value>'.format(p), param)))
    if len(param) > 1:
        return f'<additionalAttribute><additionalAttributeName>{attribute_name.upper()}</additionalAttributeName><additionalAttributeValue><list>' + values + '</list></additionalAttributeValue></additionalAttribute>'
    else:
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
    startDate, endDate, season = val.split(',')
    startyear, startMonth, startDay = startDate.split('-')[0:3]
    startDay = startDay.split('T')[0]
    endYear, endMonth, endDay = endDate.split('-')[0:3]
    endDay = endDay.split('T')[0]
    return f'<granuleCondition><{key}>' + ('' if startDate == None else  f'<startDate><Date YYYY=\"{startyear}\" MM=\"{startMonth}\" DD=\"{startDay}\"></Date></startDate>') + ('' if endDate == None else  f'<stopDate><Date YYYY=\"{endYear}\" MM=\"{endMonth}\" DD=\"{endDay}\"></Date></stopDate>') + f'</{key}></granuleCondition>'

def default_enddate(val: datetime, key):
    # processingDate = date().today().strftime('%Y-%m-%dT%H:%M:%SZ')
    startyear  = val.year
    startMonth = val.month
    startDay = val.day
    # startDay = startDay.split('T')[0]
    # endYear, endMonth, endDay = endDate.split('-')[0:3]processingDate
    return f'<granuleCondition><{key}><dateRange>' + f'<startDate><Date YYYY=\"{startyear}\" MM=\"{startMonth}\" DD=\"{startDay}\"></Date></startDate>' + f'</dateRange></{key}></granuleCondition>'

    # endDate = date().today().strftime('%Y-%m-%dT%H:%M:%SZ')
    # return to_temporal(val + ',' + val + ',', key)

def to_defined_aql_field(param, key, operator=None):
    # for non-additional attribute format (CMR defined fields)
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

    # if len(param) > 1:
    #     param_range = param_range.format([])

    return param_range

def to_platform_field(val, key):
    return to_defined_aql_field(val, key, 'OR')

aql_field_map = {
    # API parameter               CMR keyword                       CMR format strings
    'absoluteOrbit':        {'key': 'orbit_number',            'fmt': '{0}', 'attr': 'orbitNumber', 'conv': to_range_aql_field},
    'granule_list':         {'key': 'readable_granule_name[]', 'fmt': '{0}', 'attr': 'ProducerGranuleID', 'conv': to_defined_aql_field},
    'instrument':           {'key': 'instrument[]',            'fmt': '{0}', 'attr': 'instrumentShortName', 'conv': to_defined_aql_field},

    'product_list':         {'key': 'granule_ur[]',            'fmt': '{0}', 'attr': 'GranuleUR', 'conv': to_defined_aql_field},
    # 'provider':             {'key': 'provider',                'fmt': '{0}'},


    # CMR DEFINED AQL ATTRIBUTES
    
    'linestring':           {'key': 'line',                    'conv': cmr_format_to_spatial},
    'point':                {'key': 'point',                   'conv': cmr_format_to_spatial},
    'polygon':              {'key': 'polygon',                 'conv': cmr_format_to_spatial},
    'temporal':             {'key': 'temporal',                'fmt': '{0}', 'attr': 'temporal', 'conv': to_temporal},
    'processingDate':       {'key': 'updated_since',            'attr': 'ECHOLastUpdate', 'conv': default_enddate},
    
    # ADDITIONAL ATTRIBUTES
    'asfFrame':             {'key': 'attribute[]',             'attr': 'FRAME_NUMBER', 'conv': to_aql_attribute_field},
    'asfPlatform':          {'key': 'attribute[]',                 'attr': 'ASF_PLATFORM', 'conv': to_aql_attribute_field},
    'maxBaselinePerp':      {'key': 'attribute[]',               'attr': 'INSAR_BASELINE', 'conv': to_aql_attribute_field},
    'minBaselinePerp':      {'key': 'attribute[]',               'attr': 'INSAR_BASELINE', 'conv': to_aql_attribute_field},
    'bbox':                 {'key': 'bounding_box',            'conv': cmr_format_to_spatial},
    'beamMode':             {'key': 'attribute[]',                    'attr': 'BEAM_MODE', 'conv': to_aql_attribute_field},
    'beamSwath':            {'key': 'attribute[]',               'attr': 'BEAM_MODE_TYPE', 'conv': to_aql_attribute_field},
    'campaign':             {'key': 'attribute[]',                 'attr': 'MISSION_NAME', 'conv': to_aql_attribute_field},
    'maxDoppler':           {'key': 'attribute[]',                      'attr': 'DOPPLER', 'conv': to_aql_attribute_field},
    'minDoppler':           {'key': 'attribute[]',                      'attr': 'DOPPLER', 'conv': to_aql_attribute_field},
    'maxFaradayRotation':   {'key': 'attribute[]',                     'attr': 'FARADAY_ROTATION', 'conv': to_aql_attribute_field},
    'minFaradayRotation':   {'key': 'attribute[]',                     'attr': 'FARADAY_ROTATION', 'conv': to_aql_attribute_field},
    'flightDirection':      {'key': 'attribute[]',                     'attr': 'ASCENDING_DESCENDING', 'conv': to_aql_attribute_field},
    'flightLine':           {'key': 'attribute[]',                      'attr': 'FLIGHT_LINE', 'conv': to_aql_attribute_field},
    'frame':                {'key': 'attribute[]',                    'attr': 'CENTER_ESA_FRAME', 'conv': to_aql_attribute_field},
    'groupID':              {'key': 'attribute[]',              'attr': 'GROUP_ID', 'conv': to_aql_attribute_field},
    'insarStackId':         {'key': 'attribute[]',              'attr': 'INSAR_STACK_ID', 'conv': to_aql_attribute_field},
    'lookDirection':        {'key': 'attribute[]',             'attr': 'LOOK_DIRECTION', 'conv': to_aql_attribute_field},
    'maxInsarStackSize':    {'key': 'attribute[]',             'attr': 'INSAR_STACK_SIZE', 'conv': to_aql_attribute_field},
    'minInsarStackSize':    {'key': 'attribute[]',              'attr': 'INSAR_STACK_SIZE', 'conv': to_aql_attribute_field},
    'offNadirAngle':        {'key': 'attribute[]',             'attr': 'OFF_NADIR_ANGLE',         'conv': to_aql_attribute_field},
    'platform':             {'key': 'platform[]',              'attr': 'sourceName',            'conv': to_platform_field},
    'polarization':         {'key': 'attribute[]',             'attr': 'POLARIZATION',            'conv': to_aql_attribute_field},
    'processingLevel':      {'key': 'attribute[]',              'attr': 'PROCESSING_TYPE', 'conv': to_aql_attribute_field},
    'relativeOrbit':        {'key': 'attribute[]',              'attr': 'PATH_NUMBER', 'conv': to_aql_attribute_field},
}

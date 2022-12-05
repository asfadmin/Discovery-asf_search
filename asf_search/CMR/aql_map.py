from datetime import datetime
import xml.etree.ElementTree as ET
# use for CMR "additional attribute" fields
def additional_attribute_to_aql_field(param, attribute_name: str) -> str:
    root = ET.Element('additionalAttribute')
    attribute_name_element = ET.Element('additionalAttributeName')
    attribute_name_element.text = attribute_name.upper()
    attribute_values = ET.Element('additionalAttributeValue')

    if not type(param) is list:
        e = ET.Element('value')
        e.text = str(param)
        attribute_values.append(e)
        # param = [param]
    else:
        param_list = ET.Element('list')
        for p in param:
            e = ET.Element('value')
            e.text = str(p)
            param_list.append(e)
        attribute_values.append(param_list)
    
    root.append(attribute_name_element)
    root.append(attribute_values)
    return root
    # values = ''.join(list(map(lambda p: '<value>{0}</value>'.format(p), param)))
    
    # if len(param) > 1:
    #     values = f'<list>{values}</list>'

    # return f'<additionalAttribute><additionalAttributeName>{attribute_name.upper()}</additionalAttributeName><additionalAttributeValue>' + values + '</additionalAttributeValue></additionalAttribute>'

def cmr_format_to_spatial(val, param: str):
    spatial = ET.Element('spatial') # '<spatial>{0}</spatial>'
    if param == 'point':
        spatial.append(to_IIMSPoint(val))
    elif param == 'polygon':
        spatial.append(to_IIMSPolygon(val))
    elif param == 'bounding_box':
        spatial.append(to_IIMSBox(val))
    elif param == 'line':
        spatial.append(to_IIMSLine(val))

    return spatial

def to_IIMSPoint(val: str):
    lon, lat = val.split(',')
    return ET.Element('IIMSPoint', {'lat': lat, 'long': lon})
    # return f'<IIMSPoint lat=\"{lat}\" long=\"{lon}\"></IIMSPoint>'

def to_IIMSPoints(val: str):
    coords = val.split(',')
    points_iter = iter(coords)
    
    points = []
    
    # iterated coordinates by two (long, lat)
    for x, y in zip(points_iter, points_iter):
        points.append(x + ',' + y)
    
    output = [to_IIMSPoint(point) for point in points]
    return output

def to_IIMSLine(val: str):
    root = ET.Element('IIMSLine')
    root.extend(to_IIMSPoints(val))
    
    return root
    # return '<IIMSLine>' + to_IIMSPoints(val) + '</IIMSLine>'
    
def to_IIMSPolygon(val: str):
    root = ET.Element('IIMSPolygon')
    ring = ET.Element('IIMSLRing')
    ring.extend(to_IIMSPoints(val))
    root.append(ring)

    return root
    # return '<IIMSPolygon><IIMSLRing>' + to_IIMSPoints(val) + '</IIMSLRing></IIMSPolygon>'

def to_IIMSBox(val: str):
    root = ET.Element('IIMSBox')
    root.extend(to_IIMSPoints(val))
    return root
    # return '<IIMSBox>' + to_IIMSPoints(val) + '</IIMSBox>'

def to_temporal(val, key):
    temporal_vals = val.split(',')
    start_date, end_date, season_range = (temporal_vals[0], temporal_vals[1], temporal_vals[2:])
    
    start_year, start_month, start_day = start_date.split('-')[0:3]
    start_day = start_day.split('T')[0]
    
    end_year, end_month, end_day = end_date.split('-')[0:3]
    end_day = end_day.split('T')[0]
    
    season_start = None
    season_end = None
    if len(season_range) > 1:
        start, end = season_range
        season_start = ET.Element('startDay', {'value': start})
        season_end = ET.Element('endDay', {'value': end})
        
        # season = f'<startDay value=\'{season_start}\'></startDay><endDay value=\'{season_end}\'></endDay>'
    
    root = ET.Element(key)
    start = to_date_aql_field(start_year, start_month, start_day, 'startDate')
    end = to_date_aql_field(end_year, end_month, end_day, 'stopDate')
    
    root.append(start)
    root.append(end)
    if season_start != None:
        root.append(season_start)
        root.append(season_end)

    return root
    # return f'<{key}>{start}{end}{season}</{key}>'

def to_date_aql_field(year, month, day, date_field):
    root = ET.Element(date_field)
    root.append(ET.Element('Date', {'YYY': year, 'MM': month, 'DD': day}))
    return root
    # return f'<{dateName}><Date YYYY=\"{year}\" MM=\"{month}\" DD=\"{day}\"></Date></{dateName}>'

def default_enddate(val: datetime, key):
    start_year = val.year
    start_month = val.month
    start_day = val.day
    
    root = ET.Element('key')
    date_range = ET.Element('dateRange')
    root.append(date_range)
    
    date_range.append(to_date_aql_field(start_year, start_month, start_day, 'startDate'))
    # return f'<{key}><dateRange>' + to_date_aql_field(start_year, start_month, start_day, 'startDate') + f'</dateRange></{key}>'
    return root

def to_defined_aql_field(param, key, operator=None):
    # for built-in CMR AQL fields 
    
    root = ET.Element(key)

    if not type(param) is list:
        e = ET.Element('value', {})
        e.text = str(param)
        root.append(e)
    else:
        if operator != None:
            root.attrib['operator'] = operator
        param_list = ET.Element('list')
        root.append(param_list)
        for p in param:
            e = ET.Element('value')
            e.text = str(p)
            param_list.append(e)
    #     param = [param]
        
    # for p in param:
    # values = ''.join(list(map(lambda p: '<value>{0}</value>'.format(p), param)))

    # if len(param) > 1:
    #     return f'<{key}' + ((f' operator=' + f'\"{operator}\"') if operator else '') + '><list>' + values + f'</list></{key}>'
    # else:
    #     return f'<{key}>' + values + f'</{key}>'
    
    return root

def to_range_aql_field(param, key):
    lower = param[0]
    upper = ''

    if len(param) > 1:
        upper = param[1]
    
    root = ET.Element(key)
    root.append(ET.Element('range', {'lower': lower, 'upper': upper}))
    # param_range = f"<{key}><range lower='{lower}' {upper}></range></{key}>"

    return root

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
    # 'platform':             {'aql_key': 'ASF_PLATFORM',               'conv': additional_attribute_to_aql_field},
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
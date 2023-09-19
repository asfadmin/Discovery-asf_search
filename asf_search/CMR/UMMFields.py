from asf_search.CMR.translate import get_state_vector

# common UMM properties and their UMM paths

umm_property_paths = {
        'beamModeType': ['AdditionalAttributes', ('Name', 'BEAM_MODE_TYPE'), 'Values', 0],
        'browse': ['RelatedUrls', ('Type', [('GET RELATED VISUALIZATION', 'URL')])],
        'bytes': [ 'AdditionalAttributes', ('Name', 'BYTES'), 'Values', 0],
        'centerLat': [ 'AdditionalAttributes', ('Name', 'CENTER_LAT'), 'Values', 0],
        'centerLon': [ 'AdditionalAttributes', ('Name', 'CENTER_LON'), 'Values', 0],
        'faradayRotation': [ 'AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0],
        'fileID': [ 'GranuleUR'],
        'flightDirection': [ 'AdditionalAttributes', ('Name', 'ASCENDING_DESCENDING'), 'Values', 0],
        'groupID': [ 'AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0],
        'granuleType': [ 'AdditionalAttributes', ('Name', 'GRANULE_TYPE'), 'Values', 0],
        'insarStackId': [ 'AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0],
        'md5sum': [ 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0],
        'offNadirAngle': [ 'AdditionalAttributes', ('Name', 'OFF_NADIR_ANGLE'), 'Values', 0],
        'orbit': [ 'OrbitCalculatedSpatialDomains', 0, 'OrbitNumber'],
        'pathNumber': [ 'AdditionalAttributes', ('Name', 'PATH_NUMBER'), 'Values', 0],
        'platform': [ 'AdditionalAttributes', ('Name', 'ASF_PLATFORM'), 'Values', 0],
        'pointingAngle': [ 'AdditionalAttributes', ('Name', 'POINTING_ANGLE'), 'Values', 0],
        'polarization': [ 'AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values', 0],
        'processingDate': [ 'DataGranule', 'ProductionDateTime'],
        'processingLevel': [ 'AdditionalAttributes', ('Name', 'PROCESSING_TYPE'), 'Values', 0],
        'sceneName': [ 'DataGranule', 'Identifiers', ('IdentifierType', 'ProducerGranuleId'), 'Identifier'],
        'sensor': [ 'Platforms', 0, 'Instruments', 0, 'ShortName'],
        'startTime': [ 'TemporalExtent', 'RangeDateTime', 'BeginningDateTime'],
        'stopTime': [ 'TemporalExtent', 'RangeDateTime', 'EndingDateTime'],
        'url': [ 'RelatedUrls', ('Type', 'GET DATA'), 'URL'],
        'pgeVersion': ['PGEVersionClass', 'PGEVersion'],
        'frameNumber': ['AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0],
        # 'frameNumber': ['AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0],

        # baseline (state vectors)
        'ascendingNodeTime': ['AdditionalAttributes', ('Name', 'ASC_NODE_TIME'), 'Values', 0],
        'sv_position_pre': ['AdditionalAttributes', ('Name', 'SV_POSITION_PRE'), 'Values', 0],
        'sv_position_post': ['AdditionalAttributes', ('Name', 'SV_POSITION_POST'), 'Values', 0],
        'sv_velocity_pre': ['AdditionalAttributes', ('Name', 'SV_VELOCITY_PRE'), 'Values', 0],
        'sv_velocity_post': ['AdditionalAttributes', ('Name', 'SV_VELOCITY_POST'), 'Values', 0],

        # baseline (precalc)
        'insarBaseline': ['AdditionalAttributes', ('Name', 'INSAR_BASELINE'), 'Values', 0],
        
        # bursts
        'absoluteBurstID': ['AdditionalAttributes', ('Name', 'BURST_ID_ABSOLUTE'), 'Values', 0],
        'relativeBurstID': ['AdditionalAttributes', ('Name', 'BURST_ID_RELATIVE'), 'Values', 0],
        'fullBurstID': ['AdditionalAttributes', ('Name', 'BURST_ID_FULL'), 'Values', 0],
        'burstIndex': ['AdditionalAttributes', ('Name', 'BURST_INDEX'), 'Values', 0],
        'samplesPerBurst': ['AdditionalAttributes', ('Name', 'SAMPLES_PER_BURST'), 'Values', 0],
        'subswath': ['AdditionalAttributes', ('Name', 'SUBSWATH_NAME'), 'Values', 0],
        'azimuthTime': ['AdditionalAttributes', ('Name', 'AZIMUTH_TIME'), 'Values', 0],
        'azimuthAnxTime': ['AdditionalAttributes', ('Name', 'AZIMUTH_ANX_TIME'), 'Values', 0],
        'RelatedUrls': ['RelatedUrls', ('Type', [('USE SERVICE API', 'URL')]), 0],
        'byteLength': ['AdditionalAttributes', ('Name', 'BYTE_LENGTH'),  'Values', 0], # alt for bytes
        
        # Platform/Product specific overrides
        'S1AlosFrameNumber': ['AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0], #Sentinel and ALOS product alt for frameNumber (ESA_FRAME)
        
        # Fallbacks
        'platformShortName': ['Platforms', 0, 'ShortName'], # fallback for 'platform'
        'beamMode': ['AdditionalAttributes', ('Name', 'BEAM_MODE'), 'Values', 0] # fallback to 'beamModeType'
    }

def float_string_as_int(val):
    int(float(val))

umm_property_typecasting = {
    'bytes': float_string_as_int, # casting the string literal of a floating point number raises a TypeError, parse as float first
    'centerLat': float,
    'centerLon': float,
    'faradayRotation': float,
    'offNadirAngle': float,
    'orbit': int,
    'pathNumber': int,
    'pointingAngle': float,
    'frameNumber': int,
    'sv_position_pre': get_state_vector,
    'sv_position_post': get_state_vector,
    'sv_velocity_pre': get_state_vector,
    'sv_velocity_post': get_state_vector,
    'absoluteBurstID': int,
    'relativeBurstID': int,
    'burstIndex': int,
    'samplesPerBurst': int,
    'byteLength': int
}

# properties = {
#         'beamModeType': get(umm, 'AdditionalAttributes', ('Name', 'BEAM_MODE_TYPE'), 'Values', 0),
#         'browse': get(umm, 'RelatedUrls', ('Type', [('GET RELATED VISUALIZATION', 'URL')])),
#         'bytes': cast(int, try_round_float(get(umm, 'AdditionalAttributes', ('Name', 'BYTES'), 'Values', 0))),
#         'centerLat': cast(float, get(umm, 'AdditionalAttributes', ('Name', 'CENTER_LAT'), 'Values', 0)),
#         'centerLon': cast(float, get(umm, 'AdditionalAttributes', ('Name', 'CENTER_LON'), 'Values', 0)),
#         'faradayRotation': cast(float, get(umm, 'AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0)),
#         'fileID': get(umm, 'GranuleUR'),
#         'flightDirection': get(umm, 'AdditionalAttributes', ('Name', 'ASCENDING_DESCENDING'), 'Values', 0),
#         'groupID': get(umm, 'AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0),
#         'granuleType': get(umm, 'AdditionalAttributes', ('Name', 'GRANULE_TYPE'), 'Values', 0),
#         'insarStackId': get(umm, 'AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0),
#         'md5sum': get(umm, 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0),
#         'offNadirAngle': cast(float, get(umm, 'AdditionalAttributes', ('Name', 'OFF_NADIR_ANGLE'), 'Values', 0)),
#         'orbit': cast(int, get(umm, 'OrbitCalculatedSpatialDomains', 0, 'OrbitNumber')),
#         'pathNumber': cast(int, get(umm, 'AdditionalAttributes', ('Name', 'PATH_NUMBER'), 'Values', 0)),
#         'platform': get(umm, 'AdditionalAttributes', ('Name', 'ASF_PLATFORM'), 'Values', 0),
#         'pointingAngle': cast(float, get(umm, 'AdditionalAttributes', ('Name', 'POINTING_ANGLE'), 'Values', 0)),
#         'polarization': get(umm, 'AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values', 0),
#         'processingDate': get(umm, 'DataGranule', 'ProductionDateTime'),
#         'processingLevel': get(umm, 'AdditionalAttributes', ('Name', 'PROCESSING_TYPE'), 'Values', 0),
#         'sceneName': get(umm, 'DataGranule', 'Identifiers', ('IdentifierType', 'ProducerGranuleId'), 'Identifier'),
#         'sensor': get(umm, 'Platforms', 0, 'Instruments', 0, 'ShortName'),
#         'startTime': get(umm, 'TemporalExtent', 'RangeDateTime', 'BeginningDateTime'),
#         'stopTime': get(umm, 'TemporalExtent', 'RangeDateTime', 'EndingDateTime'),
#         'url': get(umm, 'RelatedUrls', ('Type', 'GET DATA'), 'URL'),
#         'pgeVersion': get(umm, 'PGEVersionClass', 'PGEVersion')
#     }
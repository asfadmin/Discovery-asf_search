field_map = {
    # API parameter                 CMR keyword                         CMR format strings
    'absoluteOrbit':                {'key': 'orbit_number',             'fmt': '{0}'},
    'asfFrame':                     {'key': 'attribute[]',              'fmt': 'int,FRAME_NUMBER,{0}'},
    'maxBaselinePerp':              {'key': 'attribute[]',              'fmt': 'float,INSAR_BASELINE,,{0}'},
    'minBaselinePerp':              {'key': 'attribute[]',              'fmt': 'float,INSAR_BASELINE,{0},'},
    'bbox':                         {'key': 'bounding_box',             'fmt': '{0}'},
    'beamMode':                     {'key': 'attribute[]',              'fmt': 'string,BEAM_MODE,{0}'},
    'beamSwath':                    {'key': 'attribute[]',              'fmt': 'string,BEAM_MODE_TYPE,{0}'},
    'campaign':                     {'key': 'attribute[]',              'fmt': 'string,MISSION_NAME,{0}'},
    'circle':                       {'key': 'circle',                   'fmt': '{0}'},
    'maxDoppler':                   {'key': 'attribute[]',              'fmt': 'float,DOPPLER,,{0}'},
    'minDoppler':                   {'key': 'attribute[]',              'fmt': 'float,DOPPLER,{0},'},
    'maxFaradayRotation':           {'key': 'attribute[]',              'fmt': 'float,FARADAY_ROTATION,,{0}'},  # noqa F401
    'minFaradayRotation':           {'key': 'attribute[]',              'fmt': 'float,FARADAY_ROTATION,{0},'},  # noqa F401
    'flightDirection':              {'key': 'attribute[]',              'fmt': 'string,ASCENDING_DESCENDING,{0}'},  # noqa F401
    'flightLine':                   {'key': 'attribute[]',              'fmt': 'string,FLIGHT_LINE,{0}'},
    'frame':                        {'key': 'attribute[]',              'fmt': 'int,CENTER_ESA_FRAME,{0}'},
    'granule_list':                 {'key': 'readable_granule_name[]',  'fmt': '{0}'},
    'groupID':                      {'key': 'attribute[]',              'fmt': 'string,GROUP_ID,{0}'},
    'insarStackId':                 {'key': 'attribute[]',              'fmt': 'int,INSAR_STACK_ID,{0}'},
    'linestring':                   {'key': 'line',                     'fmt': '{0}'},
    'lookDirection':                {'key': 'attribute[]',              'fmt': 'string,LOOK_DIRECTION,{0}'},
    'maxInsarStackSize':            {'key': 'attribute[]',              'fmt': 'int,INSAR_STACK_SIZE,,{0}'},
    'minInsarStackSize':            {'key': 'attribute[]',              'fmt': 'int,INSAR_STACK_SIZE,{0},'},
    'instrument':                   {'key': 'instrument[]',             'fmt': '{0}'},
    'offNadirAngle':                {'key': 'attribute[]',              'fmt': 'float,OFF_NADIR_ANGLE,{0}'},
    'platform':                     {'key': 'platform[]',               'fmt': '{0}'},
    'polarization':                 {'key': 'attribute[]',              'fmt': 'string,POLARIZATION,{0}'},
    'point':                        {'key': 'point',                    'fmt': '{0}'},
    'polygon':                      {'key': 'polygon',                  'fmt': '{0}'},
    'processingDate':               {'key': 'updated_since',            'fmt': '{0}'},
    'processingLevel':              {'key': 'attribute[]',              'fmt': 'string,PROCESSING_TYPE,{0}'},
    'product_list':                 {'key': 'granule_ur[]',             'fmt': '{0}'},
    'provider':                     {'key': 'provider',                 'fmt': '{0}'},
    'relativeOrbit':                {'key': 'attribute[]',              'fmt': 'int,PATH_NUMBER,{0}'},
    'temporal':                     {'key': 'temporal',                 'fmt': '{0}'},
    'collections':                  {'key': 'echo_collection_id[]',     'fmt': '{0}'},
    'shortName':                    {'key': 'shortName',                'fmt': '{0}'},
    'temporalBaselineDays':         {'key': 'attribute[]',              'fmt': 'int,TEMPORAL_BASELINE_DAYS,{0}'},  # noqa F401
    # SLC BURST fields
    'absoluteBurstID':              {'key': 'attribute[]',              'fmt': 'int,BURST_ID_ABSOLUTE,{0}'},
    'relativeBurstID':              {'key': 'attribute[]',              'fmt': 'int,BURST_ID_RELATIVE,{0}'},
    'fullBurstID':                  {'key': 'attribute[]',              'fmt': 'string,BURST_ID_FULL,{0}'},
    # OPERA-S1 field
    'operaBurstID':                 {'key': 'attribute[]',              'fmt': 'string,OPERA_BURST_ID,{0}'},
    # NISAR fields
    'mainBandPolarization':         {'key': 'attribute[]',             'fmt': 'string,FREQUENCY_A_POLARIZATION_CONCAT,{0}'},
    'sideBandPolarization':         {'key': 'attribute[]',             'fmt': 'string,FREQUENCY_B_POLARIZATION_CONCAT,{0}'},
    'frameCoverage':                {'key': 'attribute[]',             'fmt': 'string,FULL_FRAME,{0}'},
    'jointObservation':             {'key': 'attribute[]',             'fmt': 'string,JOINT_OBSERVATION,{0}'},
    'rangeBandwidth':               {'key': 'attribute[]',             'fmt': 'string,RANGE_BANDWIDTH_CONCAT,{0}'},
}

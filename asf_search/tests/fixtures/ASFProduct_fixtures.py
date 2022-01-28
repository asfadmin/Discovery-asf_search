import pytest

@pytest.fixture
def basic_response():
    return {
        "geometry": {
            "coordinates": [
            [
                [
                -156.42279,
                81.909
                ],
                [
                -141.93079,
                74.072
                ],
                [
                -132.77879,
                56.883
                ],
                [
                -116.70479,
                -14.862
                ],
                [
                -105.02479,
                -48.262
                ],
                [
                -93.73979,
                -62.451
                ],
                [
                -80.32579,
                -70.237
                ],
                [
                -61.41179,
                -75.082
                ],
                [
                -28.54879,
                -77.358
                ],
                [
                -28.59879,
                -86.386
                ],
                [
                -72.72279,
                -84.998
                ],
                [
                -99.16579,
                -79.734
                ],
                [
                -107.40579,
                -74.098
                ],
                [
                -116.49779,
                -57.146
                ],
                [
                -132.82479,
                15.541
                ],
                [
                -144.96879,
                49.39
                ],
                [
                -153.65679,
                60.693
                ],
                [
                -166.04779,
                68.968
                ],
                [
                -179.999,
                73.252441
                ],
                [
                -179.999,
                84.661675
                ],
                [
                -156.42279,
                81.909
                ]
            ]
            ],
            "type": "Polygon"
        },
        "properties": {
            "beamModeType": "STD",
            "browse": [],
            "bytes": "985537904.0",
            "faradayRotation": None,
            "fileID": "SP_37287_A_008-L1A_Radar_RO_HDF5",
            "fileName": "SMAP_L1A_RADAR_37287_A_20220124T015142_R18240_001.h5",
            "flightDirection": "DESCENDING",
            "frameNumber": "1860",
            "granuleType": "SMAP_SWATH",
            "groupID": "SP_37287_A_008",
            "insarStackId": "-1",
            "md5sum": "9bdf4c212fb79b62f470ab9f4465ceaa",
            "offNadirAngle": None,
            "orbit": "37287",
            "pathNumber": "0",
            "platform": "SMAP",
            "pointingAngle": None,
            "polarization": None,
            "processingDate": "2022-01-24T05:01:02Z",
            "processingLevel": "L1A_Radar_RO_HDF5",
            "sceneName": "SP_37287_A_008",
            "sensor": "SAR",
            "startTime": "2022-01-24T01:52:57Z",
            "stopTime": "2022-01-24T02:42:10Z",
            "url": "https://datapool.asf.alaska.edu/L1A_Radar_RO_HDF5/SP/SMAP_L1A_RADAR_37287_A_20220124T015142_R18240_001.h5"
        }
    }
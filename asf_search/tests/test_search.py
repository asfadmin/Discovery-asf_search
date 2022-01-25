from asf_search.ASFSearchResults import ASFSearchResults
import pytest

def test_ASFSearchResults(alos_search_results):
    search_results = ASFSearchResults(alos_search_results)

    assert(len(search_results) == 5)    


    for (idx, feature) in enumerate(search_results.data):
        assert(feature == alos_search_results[idx])

@pytest.fixture
def alos_search_results():
  return [
    {
      "geometry": {
        "coordinates": [
          [
            [
              -136.125,
              56.538
            ],
            [
              -136.295,
              57.037
            ],
            [
              -135.227,
              57.142
            ],
            [
              -135.071,
              56.643
            ],
            [
              -136.125,
              56.538
            ]
          ]
        ],
        "type": "Polygon"
      },
      "properties": {
        "beamModeType": "FBS",
        "browse": [
          "https://datapool.asf.alaska.edu/BROWSE/A3/ALPSRP111041130.jpg",
          "https://datapool.asf.alaska.edu/BROWSE/A3/AP_11104_FBS_F1130.jpg"
        ],
        "bytes": "7445999.0",
        "faradayRotation": "0.456056",
        "fileID": "ALPSRP111041130-KMZ",
        "fileName": "AP_11104_FBS_F1130.kmz",
        "flightDirection": "ASCENDING",
        "frameNumber": "1130",
        "granuleType": "ALOS_PALSAR_SCENE",
        "groupID": "ALPSRP111041130",
        "insarStackId": "1486384",
        "md5sum": "08eeca85628b02c6bb132da0933ed1d6",
        "offNadirAngle": "34.3",
        "orbit": "11104",
        "pathNumber": "238",
        "platform": "ALOS",
        "pointingAngle": None,
        "polarization": "HH",
        "processingDate": "2015-03-14T01:22:42Z",
        "processingLevel": "KMZ",
        "sceneName": "ALPSRP111041130",
        "sensor": "PALSAR",
        "startTime": "2008-02-24T07:13:21Z",
        "stopTime": "2008-02-24T07:13:29Z",
        "url": "https://datapool.asf.alaska.edu/KMZ/A3/AP_11104_FBS_F1130.kmz"
      },
      "type": "Feature"
    },
    {
      "geometry": {
        "coordinates": [
          [
            [
              -136.125,
              56.538
            ],
            [
              -136.295,
              57.037
            ],
            [
              -135.227,
              57.142
            ],
            [
              -135.071,
              56.643
            ],
            [
              -136.125,
              56.538
            ]
          ]
        ],
        "type": "Polygon"
      },
      "properties": {
        "beamModeType": "FBS",
        "browse": [
          "https://datapool.asf.alaska.edu/BROWSE/A3/ALPSRP111041130.jpg",
          "https://datapool.asf.alaska.edu/BROWSE/A3/AP_11104_FBS_F1130.jpg"
        ],
        "bytes": "408738585",
        "faradayRotation": "0.456056",
        "fileID": "ALPSRP111041130-L1.0",
        "fileName": "ALPSRP111041130-L1.0.zip",
        "flightDirection": "ASCENDING",
        "frameNumber": "1130",
        "granuleType": "ALOS_PALSAR_SCENE",
        "groupID": "ALPSRP111041130",
        "insarStackId": "1486384",
        "md5sum": "2a5fa75a25f9eb8d176ffd5bf1bfab21",
        "offNadirAngle": "34.3",
        "orbit": "11104",
        "pathNumber": "238",
        "platform": "ALOS",
        "pointingAngle": None,
        "polarization": "HH",
        "processingDate": "2012-08-23T00:00:00Z",
        "processingLevel": "L1.0",
        "sceneName": "ALPSRP111041130",
        "sensor": "PALSAR",
        "startTime": "2008-02-24T07:13:21Z",
        "stopTime": "2008-02-24T07:13:29Z",
        "url": "https://datapool.asf.alaska.edu/L1.0/A3/ALPSRP111041130-L1.0.zip"
      },
      "type": "Feature"
    },
    {
      "geometry": {
        "coordinates": [
          [
            [
              -136.125,
              56.538
            ],
            [
              -136.295,
              57.037
            ],
            [
              -135.227,
              57.142
            ],
            [
              -135.071,
              56.643
            ],
            [
              -136.125,
              56.538
            ]
          ]
        ],
        "type": "Polygon"
      },
      "properties": {
        "beamModeType": "FBS",
        "browse": [
          "https://datapool.asf.alaska.edu/BROWSE/A3/ALPSRP111041130.jpg",
          "https://datapool.asf.alaska.edu/BROWSE/A3/AP_11104_FBS_F1130.jpg"
        ],
        "bytes": "181580839",
        "faradayRotation": "0.456056",
        "fileID": "ALPSRP111041130-L1.5",
        "fileName": "ALPSRP111041130-L1.5.zip",
        "flightDirection": "ASCENDING",
        "frameNumber": "1130",
        "granuleType": "ALOS_PALSAR_SCENE",
        "groupID": "ALPSRP111041130",
        "insarStackId": "1486384",
        "md5sum": "41e017b2cad8abadd7a2239cb0bd7897",
        "offNadirAngle": "34.3",
        "orbit": "11104",
        "pathNumber": "238",
        "platform": "ALOS",
        "pointingAngle": None,
        "polarization": "HH",
        "processingDate": "2012-08-23T00:00:00Z",
        "processingLevel": "L1.5",
        "sceneName": "ALPSRP111041130",
        "sensor": "PALSAR",
        "startTime": "2008-02-24T07:13:21Z",
        "stopTime": "2008-02-24T07:13:29Z",
        "url": "https://datapool.asf.alaska.edu/L1.5/A3/ALPSRP111041130-L1.5.zip"
      },
      "type": "Feature"
    },
    {
      "geometry": {
        "coordinates": [
          [
            [
              -136.125,
              56.538
            ],
            [
              -136.295,
              57.037
            ],
            [
              -135.227,
              57.142
            ],
            [
              -135.071,
              56.643
            ],
            [
              -136.125,
              56.538
            ]
          ]
        ],
        "type": "Polygon"
      },
      "properties": {
        "beamModeType": "FBS",
        "browse": [
          "https://datapool.asf.alaska.edu/BROWSE/A3/ALPSRP111041130.jpg",
          "https://datapool.asf.alaska.edu/BROWSE/A3/AP_11104_FBS_F1130.jpg"
        ],
        "bytes": "219026831.0",
        "faradayRotation": "0.456056",
        "fileID": "ALPSRP111041130-RTC_HI_RES",
        "fileName": "AP_11104_FBS_F1130_RT1.zip",
        "flightDirection": "ASCENDING",
        "frameNumber": "1130",
        "granuleType": "ALOS_PALSAR_SCENE",
        "groupID": "ALPSRP111041130",
        "insarStackId": "1486384",
        "md5sum": "d149fafa8943919abd3c5e08263dc404",
        "offNadirAngle": "34.3",
        "orbit": "11104",
        "pathNumber": "238",
        "platform": "ALOS",
        "pointingAngle": None,
        "polarization": "HH",
        "processingDate": "2015-03-14T01:23:11Z",
        "processingLevel": "RTC_HI_RES",
        "sceneName": "ALPSRP111041130",
        "sensor": "PALSAR",
        "startTime": "2008-02-24T07:13:21Z",
        "stopTime": "2008-02-24T07:13:29Z",
        "url": "https://datapool.asf.alaska.edu/RTC_HI_RES/A3/AP_11104_FBS_F1130_RT1.zip"
      },
      "type": "Feature"
    },
    {
      "geometry": {
        "coordinates": [
          [
            [
              -136.125,
              56.538
            ],
            [
              -136.295,
              57.037
            ],
            [
              -135.227,
              57.142
            ],
            [
              -135.071,
              56.643
            ],
            [
              -136.125,
              56.538
            ]
          ]
        ],
        "type": "Polygon"
      },
      "properties": {
        "beamModeType": "FBS",
        "browse": [
          "https://datapool.asf.alaska.edu/BROWSE/A3/ALPSRP111041130.jpg",
          "https://datapool.asf.alaska.edu/BROWSE/A3/AP_11104_FBS_F1130.jpg"
        ],
        "bytes": "45750549.0",
        "faradayRotation": "0.456056",
        "fileID": "ALPSRP111041130-RTC_LOW_RES",
        "fileName": "AP_11104_FBS_F1130_RT2.zip",
        "flightDirection": "ASCENDING",
        "frameNumber": "1130",
        "granuleType": "ALOS_PALSAR_SCENE",
        "groupID": "ALPSRP111041130",
        "insarStackId": "1486384",
        "md5sum": "623c4cd39a848437f0a342cbd659ea8d",
        "offNadirAngle": "34.3",
        "orbit": "11104",
        "pathNumber": "238",
        "platform": "ALOS",
        "pointingAngle": None,
        "polarization": "HH",
        "processingDate": "2015-03-14T01:22:42Z",
        "processingLevel": "RTC_LOW_RES",
        "sceneName": "ALPSRP111041130",
        "sensor": "PALSAR",
        "startTime": "2008-02-24T07:13:21Z",
        "stopTime": "2008-02-24T07:13:29Z",
        "url": "https://datapool.asf.alaska.edu/RTC_LOW_RES/A3/AP_11104_FBS_F1130_RT2.zip"
      },
      "type": "Feature"
    }
  ]
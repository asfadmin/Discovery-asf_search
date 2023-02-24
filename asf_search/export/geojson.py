import logging
import json

from asf_search import ASFProduct

def get_additional_geojson_fields(_: ASFProduct):
    return {}

def ASFSearchResults_to_geojson(rgen):
    logging.debug('translating: geojson')

    streamer = GeoJSONStreamArray(rgen)

    for p in json.JSONEncoder(indent=2, sort_keys=True).iterencode({'type': 'FeatureCollection','features':streamer}):
        yield p


class GeoJSONStreamArray(list):

    def getItem(self, p):
        for i in p.keys():
            if p[i] == 'NA' or p[i] == '':
                p[i] = None
        try:
            if float(p['offNadirAngle']) < 0:
                p['offNadirAngle'] = None
            if float(p['relativeOrbit']) < 0:
                p['relativeOrbit'] = None
        except TypeError:
            pass

        result = {
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon',
                'coordinates': [
                    [[float(c['lon']), float(c['lat'])] for c in p['shape']]
                ]
            },
            'properties': {
                'beamModeType': p['beamModeType'],
                'browse': p['browse'],
                'bytes': p['bytes'],
                'centerLat': p['centerLat'],
                'centerLon': p['centerLon'],
                'faradayRotation': p['faradayRotation'],
                'fileID': p['product_file_id'],
                'fileName': p['fileName'],
                'flightDirection': p['flightDirection'],
                'frameNumber': p['frameNumber'],
                'groupID': p['groupID'],
                'granuleType': p['granuleType'],
                'insarStackId': p['insarGrouping'],
                'md5sum': p['md5sum'],
                'offNadirAngle': p['offNadirAngle'],
                'orbit': p['absoluteOrbit'][0],
                'pathNumber': p['relativeOrbit'],
                'platform': p['platform'],
                'pointingAngle': p['pointingAngle'],
                'polarization': p['polarization'],
                'processingDate': p['processingDate'],
                'processingLevel': p['processingLevel'],
                'sceneName': p['granuleName'],
                'sensor': p['sensor'],
                'startTime': p['startTime'],
                'stopTime': p['stopTime'],
                'url': p['downloadUrl'],
            }
        }
        if 'temporalBaseline' in p.keys() or 'perpendicularBaseline' in p.keys():
            result['temporalBaseline'] = p['temporalBaseline']
            result['perpendicularBaseline'] = p['perpendicularBaseline']

        if p.get('processingLevel') == 'BURST': # is a burst product
            result['burst'] = p['burst']
        
        return result

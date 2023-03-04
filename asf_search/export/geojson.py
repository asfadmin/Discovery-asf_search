import logging
import json

def ASFSearchResults_to_geojson(rgen):
    logging.debug('translating: geojson')

    streamer = GeoJSONStreamArray(rgen)

    for p in json.JSONEncoder(indent=2, sort_keys=True).iterencode({'type': 'FeatureCollection','features':streamer}):
        yield p

class GeoJSONStreamArray(list):
    def streamDicts(self):
        for page in self.results:
            yield from [self.getItem(p) for p in page if p is not None]

    def getItem(self, p):
        return p.geojson()
    
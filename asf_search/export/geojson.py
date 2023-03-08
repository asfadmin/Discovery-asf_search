import inspect
import logging
import json
from types import GeneratorType

def results_to_geojson(results):
    logging.debug('translating: geojson')

    if not inspect.isgeneratorfunction(results) and not isinstance(results, GeneratorType):
        results = [results]
    
    streamer = GeoJSONStreamArray(results)

    for p in json.JSONEncoder(indent=2, sort_keys=True).iterencode({'type': 'FeatureCollection','features':streamer}):
        yield p

class GeoJSONStreamArray(list):
    def streamDicts(self):
        for page in self.results:
            yield from [self.getItem(p) for p in page if p is not None]

    def getItem(self, p):
        return p.geojson()

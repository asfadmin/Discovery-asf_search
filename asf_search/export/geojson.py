import inspect
import json
from types import GeneratorType

from asf_search import ASF_LOGGER

def results_to_geojson(results):
    ASF_LOGGER.info('started translating results to geojson format')

    if not inspect.isgeneratorfunction(results) and not isinstance(results, GeneratorType):
        results = [results]
    
    streamer = GeoJSONStreamArray(results)

    for p in json.JSONEncoder(indent=2, sort_keys=True).iterencode({'type': 'FeatureCollection','features':streamer}):
        yield p

class GeoJSONStreamArray(list):
    def streamDicts(self):
        
        completed = False
        for page_idx, page in enumerate(self.results):
            ASF_LOGGER.info(f"Streaming {len(page)} products from page {page_idx}")
            completed = page.searchComplete
            
            yield from [self.getItem(p) for p in page if p is not None]

        if not completed:
            ASF_LOGGER.warn('Failed to download all results from CMR')

        ASF_LOGGER.info('Finished streaming geojson results')
    
    def getItem(self, p):
        return p.geojson()

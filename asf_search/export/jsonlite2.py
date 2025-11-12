import inspect
import json
from types import GeneratorType

from asf_search import ASF_LOGGER
from .jsonlite import JSONLiteStreamArray

def results_to_jsonlite2(results):
    ASF_LOGGER.info('started translating results to jsonlite2 format')
    
    if len(results) == 0:
            yield from json.JSONEncoder(indent=2, sort_keys=True).iterencode({'results': []})
            return
        
    if not inspect.isgeneratorfunction(results) and not isinstance(results, GeneratorType):
        results = [results]

    streamer = JSONLite2StreamArray(results)

    for p in json.JSONEncoder(sort_keys=True, separators=(",", ":")).iterencode(
        {"results": streamer}
    ):
        yield p


class JSONLite2StreamArray(JSONLiteStreamArray):
    def getItem(self, p):
        # pre-processing of the result is the same as in the base jsonlite streamer,
        # so use that and then rename/substitute fields
        p = super().getItem(p)
        result = {
            "b": [a.replace(p.get("granuleName"), "{gn}") for a in p.get("browse")]
            if p["browse"] is not None
            else p["browse"],
            "bm": p.get("beamMode"),
            "d": p.get("dataset"),
            "du": p.get("downloadUrl").replace(p.get("granuleName"), "{gn}"),
            "f": p.get("frame"),
            "fd": p.get("flightDirection"),
            "fl": p.get("flightLine"),
            "fn": p.get("fileName").replace(p.get("granuleName"), "{gn}"),
            "fr": p.get("faradayRotation"),  # ALOS
            "gid": p.get("groupID").replace(p.get("granuleName"), "{gn}"),
            "gn": p.get("granuleName"),
            "i": p.get("instrument"),
            "in": p.get("canInSAR"),
            "mn": p.get("missionName"),
            "o": p.get("orbit"),
            "on": p.get("offNadirAngle"),  # ALOS
            "p": p.get("path"),
            "pid": p.get("productID").replace(p.get("granuleName"), "{gn}"),
            "pa": p.get("pointingAngle"),
            "po": p.get("polarization"),
            "pt": p.get("productType"),
            "ptd": p.get("productTypeDisplay"),
            "s": p.get("sizeMB"),
            "ss": p.get("stackSize"),  # Used for datasets with precalculated stacks
            "st": p.get("startTime"),
            "stp": p.get("stopTime"),
            "t": p.get("thumb").replace(p.get("granuleName"), "{gn}")
            if p.get("thumb") is not None
            else p.get("thumb"),
            "w": p.get("wkt"),
            "wu": p.get("wkt_unwrapped"),
            "pge": p.get("pgeVersion"),
            "adu": p.get("additionalUrls"),
            's3u': p.get("s3Urls"),
        }

        if 'temporalBaseline' in p.keys():
            result['tb'] = p['temporalBaseline']
        if 'perpendicularBaseline' in p.keys():
            result['pb'] = p['perpendicularBaseline']

        if p.get('burst') is not None: # is a burst product
            result['s1b'] = p['burst']
            result['f'] = None

        if p.get('opera') is not None:
            result['s1o'] = p['opera']
        
        if p.get('nisar') is not None:
            result['nsr'] = p['nisar']
            result["cnm"] = p["collectionName"]
            result["cid"] = p["conceptID"]
        
        if p.get('ariaVersion') is not None:
            result['ariav'] = p.get('ariaVersion')
    
        return result

    def getOutputType(self) -> str:
        return "jsonlite2"

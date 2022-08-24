from typing import List, Dict
import logging
import json
from .jsonlite import JSONLiteStreamArray

def ASFSearchResults_to_jsonlite2(results_properties: List[Dict]):
    logging.debug('translating: jsonlite')

    streamer = JSONLite2StreamArray(results_properties)

    for p in json.JSONEncoder(sort_keys=True, separators=(',', ':')).iterencode({'results': streamer}):
        yield p


class JSONLite2StreamArray(JSONLiteStreamArray):
    def getItem(self, p):
         # pre-processing of the result is the same as in the base jsonlite streamer,
         # so use that and then rename/substitute fields
        p = super().getItem(p)
        result = {
            'b': [a.replace(p['granuleName'], '{gn}') for a in p['browse']] if p['browse'] is not None else p['browse'],
            'bm': p['beamMode'],
            'd': p['dataset'],
            'du': p['downloadUrl'].replace(p['granuleName'], '{gn}'),
            'f': p['frame'],
            'fd': p['flightDirection'],
            'fl': p['flightLine'],
            'fn': p['fileName'].replace(p['granuleName'], '{gn}'),
            'fr': p['faradayRotation'], # ALOS
            'gid': p['groupID'].replace(p['granuleName'], '{gn}'),
            'gn': p['granuleName'],
            'i': p['instrument'],
            'in': p['canInSAR'],
            'mn': p['missionName'],
            'o': p['orbit'],
            'on': p['offNadirAngle'], # ALOS
            'p': p['path'],
            'pid': p['productID'].replace(p['granuleName'], '{gn}'),
            'pa': p['pointingAngle'],
            'po': p['polarization'],
            'pt': p['productType'],
            'ptd': p['productTypeDisplay'],
            's': p['sizeMB'],
            'ss': p['stackSize'], # Used for datasets with precalculated stacks
            'st': p['startTime'],
            'stp': p['stopTime'],
            't': p['thumb'].replace(p['granuleName'], '{gn}') if p['thumb'] is not None else p['thumb'],
            'w': p['wkt'],
            'wu': p['wkt_unwrapped']
        }

        if 'temporalBaseline' in p.keys() or 'perpendicularBaseline' in p.keys():
            result['tb'] = p['temporalBaseline']
            result['pb'] = p['perpendicularBaseline']

        return result

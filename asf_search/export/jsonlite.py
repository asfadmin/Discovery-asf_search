import logging
import json
from typing import Tuple
from shapely.geometry import shape
from shapely.ops import transform

from asf_search.CMR.translate import get_additional_fields
from asf_search import ASFProduct

extra_jsonlite_fields = [
    ('processingTypeDisplay', ['AdditionalAttributes', ('Name', 'PROCESSING_TYPE_DISPLAY'), 'Values', 0]),
    ('thumb', ['AdditionalAttributes', ('Name', 'THUMBNAIL_URL'), 'Values', 0]),
    ('faradayRotation', ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0]),
    ('sizeMB', ['DataGranule', 'ArchiveAndDistributionInformation', 0, 'Size']),
    ('flightLine', ['AdditionalAttributes', ('Name', 'FLIGHT_LINE'), 'Values', 0]),
    ('missionName', ['AdditionalAttributes', ('Name', 'MISSION_NAME'), 'Values', 0]),
]

def get_additional_jsonlite_fields(product: ASFProduct):
    umm = product.umm
    
    additional_fields = {}
    for key, path in extra_jsonlite_fields:
        additional_fields[key] = get_additional_fields(umm, *path)

    if product.properties['platform'].upper() in ['ALOS', 'RADARSAT-1', 'JERS-1', 'ERS-1', 'ERS-2']:
        insarGrouping = get_additional_fields(umm, *['AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0])
        insarStackSize = get_additional_fields(umm, *['AdditionalAttributes', ('Name', 'INSAR_STACK_SIZE'), 'Values', 0])
        
        if insarGrouping not in [None, 0, '0', 'NA', 'NULL']:
            additional_fields['canInsar'] = True
            additional_fields['insarStackSize'] = insarStackSize
        else:
            additional_fields['canInsar'] = False
    else:
        additional_fields['canInsar'] = product.baseline is not None

    additional_fields['geometry'] = product.geometry

    return additional_fields

def ASFSearchResults_to_jsonlite(results):
    logging.debug('translating: jsonlite')

    streamer = JSONLiteStreamArray(results)
    jsondata = {'results': streamer}

    for p in json.JSONEncoder(indent=2, sort_keys=True).iterencode(jsondata):
        yield p

def unwrap_shape(x, y, z=None):
        x = x if x > 0 else x + 360
        return tuple([x, y])

def get_wkts(geometry) -> Tuple[str, str]:
    wrapped = shape(geometry)
    
    min_lon, max_lon = (wrapped.bounds[0], wrapped.bounds[2])
    
    if max_lon - min_lon > 180:    
        unwrapped = transform(unwrap_shape, wrapped)
    else:
        unwrapped = wrapped

    return wrapped.wkt, unwrapped.wkt

class JSONLiteStreamArray(list):
    def __init__(self, results):
        self.results = results

        # need to make sure we actually have results so we can intelligently set __len__, otherwise
        # iterencode behaves strangely and will output invalid json
        self.first_result = None
        self.len = 0
        for p in self.results:
            if p is not None:
                self.first_result = p
                self.len = 1
                break

    def __iter__(self):
        return self.streamDicts()

    def __len__(self):
        return self.len

    def streamDicts(self):
        for p in self.results:
            if p is not None:
                yield self.getItem(p)

    def getItem(self, p):
        for i in p.keys():
            if p[i] == 'NA' or p[i] == '':
                p[i] = None
        try:
            if float(p['offNadirAngle']) < 0:
                p['offNadirAngle'] = None
        except TypeError:
            pass

        try:
            if float(p['pathNumber']) < 0:
                p['pathNumber'] = None
        except TypeError:
            pass

        try:
            if p['groupID'] is None:
                p['groupID'] = p['sceneName']
        except TypeError:
            pass

        try:
            p['sizeMB'] = float(p['sizeMB'])
        except TypeError:
            pass

        try:
            p['pathNumber'] = int(p['pathNumber'])
        except TypeError:
            pass

        try:
            p['frameNumber'] = int(p['frameNumber'])
        except TypeError:
            pass

        try:
            p['orbit'] = int(p['orbit'])
        except TypeError:
            pass

        wrapped, unwrapped = get_wkts(p['geometry'])
        result = {
            'beamMode': p['beamModeType'],
            'browse': [] if p.get('browse') is None else p.get('browse'),
            'canInSAR': p['canInsar'],
            'dataset': p['platform'],
            'downloadUrl': p['url'],
            'faradayRotation': p['faradayRotation'], # ALOS
            'fileName': p['fileName'],
            'flightDirection': p['flightDirection'],
            'flightLine': p['flightLine'],
            'frame': p['frameNumber'],
            'granuleName': p['sceneName'],
            'groupID': p['groupID'],
            'instrument': p['sensor'],
            'missionName': p['missionName'],
            'offNadirAngle': str(p['offNadirAngle']) if p['offNadirAngle'] is not None else None, # ALOS
            'orbit': [str(p['orbit'])],
            'path': p['pathNumber'],
            'polarization': p['polarization'],
            'pointingAngle': p['pointingAngle'],
            'productID': p['fileID'],
            'productType': p['processingLevel'],
            'productTypeDisplay': p['processingTypeDisplay'],
            'sizeMB': p['sizeMB'],
            'stackSize': p.get('insarStackSize'), # Used for datasets with precalculated stacks
            'startTime': p['startTime'],
            'stopTime': p['stopTime'],
            'thumb': p['thumb'],
            'wkt': wrapped,
            'wkt_unwrapped': unwrapped
        }
        
        for key in result.keys():
            if result[key] in [ 'NA', 'NULL']:
                result[key] = None

        if 'temporalBaseline' in p.keys() or 'perpendicularBaseline' in p.keys():
            result['temporalBaseline'] = p['temporalBaseline']
            result['perpendicularBaseline'] = p['perpendicularBaseline']

        return result

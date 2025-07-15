import inspect
import json
import re
from types import GeneratorType
from typing import Tuple
from shapely.geometry import shape
from shapely.ops import transform

from asf_search import ASF_LOGGER
from asf_search.export.export_translators import ASFSearchResults_to_properties_list

extra_json_fields = [
    (
        'processingTypeDisplay',
        ['AdditionalAttributes', ('Name', 'PROCESSING_TYPE_DISPLAY'), 'Values', 0],
    ),
    (
        'beamMode',
        ['AdditionalAttributes', ('Name', 'BEAM_MODE'), 'Values', 0],
    ),
    ('thumbnailUrl', ['AdditionalAttributes', ('Name', 'THUMBNAIL_URL'), 'Values', 0]),
    (
        'faradayRotation',
        ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0],
    ),
    ('sizeMB', ['DataGranule', 'ArchiveAndDistributionInformation', 0, 'Size']),
    ('flightLine', ['AdditionalAttributes', ('Name', 'FLIGHT_LINE'), 'Values', 0]),
    ('missionName', ['AdditionalAttributes', ('Name', 'MISSION_NAME'), 'Values', 0]),
    ('centerLat', ['AdditionalAttributes', ('Name', 'CENTER_LAT'), 'Values', 0]),
    ('centerLon', ['AdditionalAttributes', ('Name', 'CENTER_LON'), 'Values', 0]),
    ('configurationName', ['AdditionalAttributes', ('Name', 'BEAM_MODE_DESC'), 'Values', 0]),
    ('doppler', ['AdditionalAttributes', ('Name', 'DOPPLER'), 'Values', 0]),
    ('nearStartLat', ['AdditionalAttributes', ('Name', 'NEAR_START_LAT'), 'Values', 0]),
    ('nearStartLon', ['AdditionalAttributes', ('Name', 'NEAR_START_LON'), 'Values', 0]),
    ('farStartLat', ['AdditionalAttributes', ('Name', 'FAR_START_LAT'), 'Values', 0]),
    ('farStartLon', ['AdditionalAttributes', ('Name', 'FAR_START_LON'), 'Values', 0]),
    ('nearEndLat', ['AdditionalAttributes', ('Name', 'NEAR_END_LAT'), 'Values', 0]),
    ('nearEndLon', ['AdditionalAttributes', ('Name', 'NEAR_END_LON'), 'Values', 0]),
    ('farEndLat', ['AdditionalAttributes', ('Name', 'FAR_END_LAT'), 'Values', 0]),
    ('farEndLon', ['AdditionalAttributes', ('Name', 'FAR_END_LON'), 'Values', 0]),
    (
        'faradayRotation',
        ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0],
    ),
    (
        'finalFrame',
        ['AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0],
    ),
    (
        'firstFrame',
        ['AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0],
    ),
    (
        'insarStackSize',
        ['AdditionalAttributes', ('Name', 'INSAR_STACK_SIZE'), 'Values', 0],
    ),
    (
        'lookDirection',
        ['AdditionalAttributes', ('Name', 'LOOK_DIRECTION'), 'Values', 0],
    ),
    (
        'processingDescription',
        ['AdditionalAttributes', ('Name', 'PROCESSING_DESCRIPTION'), 'Values', 0],
    ),
    ('sceneDate', ['AdditionalAttributes', ('Name', 'ACQUISITION_DATE'), 'Values', 0]),
    ('processingType', ['AdditionalAttributes', ('Name', 'PROCESSING_LEVEL'), 'Values', 0]),
    ('pointingAngle', ['AdditionalAttributes', ('Name', 'POINTING_ANGLE'), 'Values', 0]),
    ('offNadirAngle', ['AdditionalAttributes', ('Name', 'OFF_NADIR_ANGLE'), 'Values', 0]),
]


def results_to_json(results):
    ASF_LOGGER.info('started translating results to json format')
    if len(results) == 0:
        yield from json.JSONEncoder(indent=2, sort_keys=True).iterencode([[]])
        return

    if not inspect.isgeneratorfunction(results) and not isinstance(results, GeneratorType):
        results = [results]

    streamer = JsonStreamArray(results)

    for p in json.JSONEncoder(indent=2, sort_keys=True).iterencode([streamer]):
        yield p


def get_wkts(geometry) -> Tuple[str, str]:
    wrapped = shape(geometry)

    min_lon, max_lon = (wrapped.bounds[0], wrapped.bounds[2])

    if max_lon - min_lon > 180:
        unwrapped = transform(unwrap_shape, wrapped)
    else:
        unwrapped = wrapped

    return wrapped.wkt, unwrapped.wkt


class JsonStreamArray(list):
    def __init__(self, results):
        self.results = results

        # need to make sure we actually have results so we can intelligently set __len__, otherwise
        # iterencode behaves strangely and will output invalid json
        self.len = 1

    def __iter__(self):
        return self.streamDicts()

    def __len__(self):
        return self.len

    def get_additional_output_fields(self, product):
        # umm = product.umm

        additional_fields = {}
        for key, path in extra_json_fields:
            additional_fields[key] = product.umm_get(product.umm, *path)

        platform = product.properties.get('platform')
        if platform is None:
            platform = ''
        if platform.upper() in [
            'ALOS',
            'RADARSAT-1',
            'JERS-1',
            'ERS-1',
            'ERS-2',
        ]:
            insarGrouping = product.umm_get(
                product.umm,
                *['AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0],
            )

            if insarGrouping not in [None, 0, '0', 'NA', 'NULL']:
                additional_fields['canInsar'] = True
                additional_fields['insarStackSize'] = product.umm_get(
                    product.umm,
                    *[
                        'AdditionalAttributes',
                        ('Name', 'INSAR_STACK_SIZE'),
                        'Values',
                        0,
                    ],
                )
            else:
                additional_fields['canInsar'] = False
        else:
            additional_fields['canInsar'] = product.baseline is not None

        additional_fields['geometry'] = product.geometry

        return additional_fields

    def streamDicts(self):
        completed = False
        for page_idx, page in enumerate(self.results):
            ASF_LOGGER.info(f'Streaming {len(page)} products from page {page_idx}')
            completed = page.searchComplete

            yield from [
                self.getItem(p)
                for p in ASFSearchResults_to_properties_list(
                    page, self.get_additional_output_fields
                )
                if p is not None
            ]

        if not completed:
            ASF_LOGGER.warn('Failed to download all results from CMR')

        ASF_LOGGER.info(f'Finished streaming {self.getOutputType()} results')

    def getItem(self, p):
        for i in p.keys():
            if p[i] == 'NA' or p[i] == '':
                p[i] = None
        try:
            if p.get('offNadirAngle') is not None and float(p['offNadirAngle']) < 0:
                p['offNadirAngle'] = None
        except TypeError:
            pass

        try:
            if p.get('patNumber'):
                if float(p['pathNumber']) < 0:
                    p['pathNumber'] = None
        except TypeError:
            pass

        try:
            if p.get('groupID') is None:
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
            p['frameNumber'] = int(p.get('frameNumber'))
        except TypeError:
            pass

        try:
            p['orbit'] = int(p['orbit'])
        except TypeError:
            pass

        wrapped, unwrapped = get_wkts(p['geometry'])

        result = {
            'absoluteOrbit': p.get('orbit'),  #
            'beamMode': p.get('beamMode'),
            'beamModeType': p.get('beamModeType'),  #
            'browse': p.get('browse'),
            'centerLat': p.get('centerLat'),
            'centerLon': p.get('centerLon'),
            'collectionName': p.get('missionName'),
            'configurationName': p.get('configurationName'),  #
            'doppler': p.get('doppler'),  #
            'downloadUrl': p.get('url'),
            'farEndLat': p.get('farEndLat'),
            'farEndLon': p.get('farEndLon'),
            'farStartLat': p.get('farStartLat'),
            'farStartLon': p.get('farStartLon'),
            'faradayRotation': p.get('faradayRotation'),
            'fileName': p.get('fileName'),
            'finalFrame': p.get('finalFrame'),
            'firstFrame': p.get('firstFrame'),
            'flightDirection': p.get('flightDirection'),
            'flightLine': p.get('flightLine'),
            'frameNumber': p.get('frameNumber'),
            'granuleName': p.get('sceneName'),
            'granuleType': p.get('granuleType'),
            'groupID': p.get('groupID'),
            'insarGrouping': p.get('insarGrouping'),
            'insarStackSize': p.get('insarStackSize'),
            'lookDirection': p.get('lookDirection'),
            'md5sum': p.get('md5sum'),
            'missionName': p.get('missionName'),
            'nearEndLat': p.get('nearEndLat'),
            'nearEndLon': p.get('nearEndLon'),
            'nearStartLat': p.get('nearStartLat'),
            'nearStartLon': p.get('nearStartLon'),  #
            'offNadirAngle': p.get('offNadirAngle'),
            'platform': p.get('platform'),
            'pointingAngle': p.get('pointingAngle'),  #
            'polarization': p.get('polarization'),
            'processingDate': p.get('processingDate'),
            'processingDescription': p.get('processingDescription'),
            'processingLevel': p.get('processingLevel'),
            'processingType': p.get('processingType'),
            'processingTypeDisplay': p.get('processingTypeDisplay'),  #
            'productName': p.get('sceneName'),
            'product_file_id': p.get('fileID'),
            'relativeOrbit': p.get('pathNumber'),
            'sceneDate': p.get('sceneDate'),  #
            'sceneId': p.get('sceneName'),  #
            'sensor': p.get('sensor'),
            'sizeMB': p.get('sizeMB'),
            'startTime': p.get('startTime'),
            'stopTime': p.get('stopTime'),
            'stringFootprint': wrapped,
            'thumbnailUrl': p.get('thumbnailUrl'),
            'track': p.get('pathNumber'),
            'subswath': p.get('subswath'),
            'pgeVersion': p.get('pgeVersion'),
        }

        for key in result.keys():
            if result[key] in ['NA', 'NULL']:
                result[key] = None

        if 'temporalBaseline' in p.keys():
            result['temporalBaseline'] = p['temporalBaseline']
        if 'perpendicularBaseline' in p.keys():
            result['perpendicularBaseline'] = p['perpendicularBaseline']

        if p.get('processingLevel') == 'BURST':  # is a burst product
            result['burst'] = p['burst']
            result['sizeMB'] = float(p['bytes']) / 1024000

        elif p.get('operaBurstID') is not None or p.get('fileID').startswith('OPERA'):
            result['opera'] = {
                'operaBurstID': p.get('operaBurstID'),
                's3Urls': p.get('s3Urls', []),
                'additionalUrls': p.get('additionalUrls'),
            }
            if p.get('validityStartDate'):
                result['opera']['validityStartDate'] = p.get('validityStartDate')
        elif p.get('platform') == 'NISAR':
            result['nisar'] = {
                'additionalUrls': p.get('additionalUrls', []),
                's3Urls': p.get('s3Urls', []),
                'pgeVersion': p.get('pgeVersion'),
                'mainBandPolarization': p.get('mainBandPolarization'),
                'sideBandPolarization': p.get('sideBandPolarization'),
                'frameCoverage': p.get('frameCoverage'),
                'jointObservation': p.get('jointObservation'),
                'rangeBandwidth': p.get('rangeBandwidth'),
            }
        elif result.get('productID', result.get('fileName', '')).startswith('S1-GUNW'):
            result.pop('perpendicularBaseline', None)
            if p.get('ariaVersion') is None:
                version_unformatted = result.get('productID', '').split('v')[-1]
                result['ariaVersion'] = re.sub(
                    r'[^0-9\.]', '', version_unformatted.replace('_', '.')
                )
            else:
                result['ariaVersion'] = p.get('ariaVersion')

        if p.get('browse') is not None and len(p['browse']) == 1:
            result['browse'] = p['browse'][0]

        return result

    def getOutputType(self) -> str:
        return 'json'


def unwrap_shape(x, y, z=None):
    x = x if x > 0 else x + 360
    return tuple([x, y])

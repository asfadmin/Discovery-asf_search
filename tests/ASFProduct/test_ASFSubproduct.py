from asf_search import Products, search, ASFSearchOptions
from asf_search.ASFSearchResults import ASFSearchResults
import json
import pytest

def run_test_ASFSubproduct(scene_names: list[str], expected_subclass: str, opts: ASFSearchOptions):
    scenes = search(granule_list=scene_names, opts=opts)

    assert sorted([scene.properties['fileID'] for scene in scenes]) == sorted(scene_names)

    for scene in scenes:
        assert expected_subclass.upper() == scene.__class__.__name__ .upper(), f'Expected scene "{scene.properties["fileID"]}" to be of ASFProduct subclass {expected_subclass}. Got {scene.__class__.__name__}'
        if isinstance(scene, Products.OPERAS1Product):
            _test_OPERAS1Product(scene)
        if isinstance(scene, Products.S1BurstProduct):
            _test_S1BurstProduct(scene)
        if isinstance(scene, Products.SEASATProduct):
            _test_SEASATProduct(scene)

    for output_format in ['geojson', 'json', 'jsonlite', 'jsonlite2', 'csv', 'metalink', 'kml']:
        try:
            _get_output(scenes, output_format)
        except BaseException as exc:
            pytest.fail(f'Failed to serialized scenes {[scene.properties["fileID"] for scene in scenes]} as output format {output_format}. Original exception: {str(exc)}')

def _test_OPERAS1Product(scene: Products.OPERAS1Product):
    processing_level = scene.properties['processingLevel']

    if processing_level in ['RTC', 'RTC-STATIC']:
        _check_properties_set(scene.properties, ['bistaticDelayCorrection'])

        if processing_level == 'RTC':
            _check_properties_set(scene.properties,['noiseCorrection', 'postProcessingFilter'])

    elif processing_level == 'DISP-S1':
        _check_properties_set(scene.properties, [
            'frameNumber', 'OperaDispStackID', 'zarrUri', 'zarrStackUri',
        ])
    
    if processing_level == 'TROPO-ZENITH':
        assert scene.properties['centerLat'] is None
        assert scene.properties['centerLon'] is None
    
def _test_SEASATProduct(scene: Products.SEASATProduct):
    assert isinstance(scene.properties['md5sum'], dict)
    assert isinstance(scene.properties['bytes'], dict)
    
    bytes_entries = scene.properties['bytes'].keys()
    _check_properties_set(scene.properties['md5sum'], bytes_entries)

def _test_S1BurstProduct(scene: Products.S1BurstProduct):
    burst_properties = [
        "absoluteBurstID",
        "relativeBurstID",
        "fullBurstID",
        "burstIndex",
        "samplesPerBurst",
        "subswath",
        "azimuthTime",
        "azimuthAnxTime",
    ]

    _check_properties_set(scene.properties['burst'], burst_properties)


def _check_properties_set(properties: dict, properties_list: list[str]):
    for prop in properties_list:
        assert properties[prop] is not None

def _get_output(scenes: ASFSearchResults, output_format: str):
    match output_format.lower():
        case 'geojson':
            return scenes.geojson()
        case 'json':
            return json.loads(''.join(scenes.json()))
        case 'jsonlite':
            return json.loads(''.join(scenes.jsonlite()))
        case 'jsonlite2':
            return json.loads(''.join(scenes.jsonlite2()))
        case 'csv':
            return ''.join(scenes.csv())
        case 'metalink':
            return ''.join(scenes.metalink())
        case 'kml':
            return scenes.kml()


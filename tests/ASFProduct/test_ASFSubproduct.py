from asf_search import ASFProduct, Products, granule_search

def run_test_ASFSubproduct(scene_names: list[str], expected_subclass: str):
    scenes = granule_search(scene_names)

    assert sorted([scene.properties['fileID'] for scene in scenes]) == sorted(scene_names)

    for scene in scenes:
        assert expected_subclass.upper() == scene.__class__.__name__ .upper(), f'Expected scene "{scene.properties["fileID"]}" to be of ASFProduct subclass {expected_subclass}. Got {scene.__class__.__name__}'
        if isinstance(scene, Products.OPERAS1Product):
            _test_OPERAS1Product(scene)
        if isinstance(scene, Products.S1BurstProduct):
            _test_S1BurstProduct(scene)

def _test_OPERAS1Product(scene: Products.OPERAS1Product):
    processing_level = scene.properties['processingLevel']

    if processing_level in ['RTC', 'RTC-STATIC']:
        _check_properties_set(scene, ['bistaticDelayCorrection'])

        if processing_level == 'RTC':
            _check_properties_set(scene,['noiseCorrection', 'postProcessingFilter'])

    elif processing_level == 'DISP-S1':
        _check_properties_set(scene, [
            'frameNumber', 'OperaDispStackID', 'zarrUri', 'zarrStackUri',
        ])
    
    if processing_level == 'TROPO-ZENITH':
        assert scene.properties['centerLat'] is None
        assert scene.properties['centerLon'] is None
    
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

    for prop in burst_properties:
        assert scene.properties['burst'][prop] is not None


def _check_properties_set(scene: ASFProduct, properties: list[str]):
    for prop in properties:
        assert scene.properties[prop] is not None

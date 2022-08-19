from math import floor
from typing import Dict, List
from asf_search.CMR import get_additional_fields
import logging
from jinja2 import Environment, PackageLoader

def get_additional_csv_fields(product):
    umm = product.umm

    extra_fields = [
        ('sceneDate', ['AdditionalAttributes', ('Name', 'ACQUISITION_DATE'), 'Values', 0]),
        ('nearStartLat', ['AdditionalAttributes', ('Name', 'NEAR_START_LAT'), 'Values', 0]),
        ('nearStartLon', ['AdditionalAttributes', ('Name', 'NEAR_START_LON'), 'Values', 0]),
        ('farStartLat', ['AdditionalAttributes', ('Name', 'FAR_START_LAT'), 'Values', 0]),
        ('farStartLon', ['AdditionalAttributes', ('Name', 'FAR_START_LON'), 'Values', 0]),
        ('nearEndLat', ['AdditionalAttributes', ('Name', 'NEAR_END_LAT'), 'Values', 0]),
        ('nearEndLon', ['AdditionalAttributes', ('Name', 'NEAR_END_LON'), 'Values', 0]),
        ('farEndLat', ['AdditionalAttributes', ('Name', 'FAR_END_LAT'), 'Values', 0]),
        ('farEndLon', ['AdditionalAttributes', ('Name', 'FAR_END_LON'), 'Values', 0]),
        ('faradayRotation', ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0]),
        ('configurationName', ['AdditionalAttributes', ('Name', 'BEAM_MODE_DESC'), 'Values', 0]),
        ('doppler', ['AdditionalAttributes', ('Name', 'DOPPLER'), 'Values', 0]),
        ('sizeMB', ['DataGranule', 'ArchiveAndDistributionInformation', 0, 'Size']),
        ('insarStackSize', ['AdditionalAttributes', ('Name', 'INSAR_STACK_SIZE'), 'Values', 0]),
    ]
    
    additional_fields = {}
    for key, path in extra_fields:
        additional_fields[key] = get_additional_fields(umm, *path)

    return additional_fields

def ASFSearchResults_to_csv(results_properties: List[Dict], includeBaseline=False, addendum=None):
    logging.debug('translating: csv')

    for product in results_properties:
        if product['offNadirAngle'] != None:
            product['offNadirAngle'] = floor(product['offNadirAngle']) if product['offNadirAngle'] == floor(product['offNadirAngle']) else product['offNadirAngle']
        product['pointingAngle'] = '' if product['pointingAngle'] == None else product['pointingAngle']
    templateEnv = Environment(
        loader=PackageLoader('asf_search.export', 'templates'),
        autoescape=True
    )

    template = templateEnv.get_template('template.csv')
    for l in template.stream(includeBaseline=includeBaseline, results=results_properties):
        yield l

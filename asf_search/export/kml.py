from math import floor
from typing import List, Dict
from asf_search.CMR import get_additional_fields
import logging
from jinja2 import Environment, PackageLoader

extra_kml_fields = [
    ('configurationName', ['AdditionalAttributes', ('Name', 'BEAM_MODE_DESC'), 'Values', 0]),
    ('faradayRotation', ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0]),
    ('processingTypeDisplay', ['AdditionalAttributes', ('Name', 'PROCESSING_TYPE_DISPLAY'), 'Values', 0]),
    ('sceneDate', ['AdditionalAttributes', ('Name', 'ACQUISITION_DATE'), 'Values', 0]),
    ('shape', ['SpatialExtent', 'HorizontalSpatialDomain', 'Geometry', 'GPolygons', 0, 'Boundary', 'Points']),
    ('thumbnailUrl', ['AdditionalAttributes', ('Name', 'THUMBNAIL_URL'), 'Values', 0]),
    ('faradayRotation', ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0]),
]

def get_additional_kml_fields(product):
    umm = product.umm
    
    additional_fields = {}
    for key, path in extra_kml_fields:
        additional_fields[key] = get_additional_fields(umm, *path)

    return additional_fields

def ASFSearchResults_to_kml(results_properties: List[Dict]):
    logging.debug('translating: kml')

    templateEnv = Environment(
        loader=PackageLoader('asf_search.export', 'templates'),
        autoescape=True
    )

    includeBaseline=False
    
    for product in results_properties:
        if product['offNadirAngle'] != None:
            product['offNadirAngle'] = floor(product['offNadirAngle']) if product['offNadirAngle'] == floor(product['offNadirAngle']) else product['offNadirAngle']

        if 'temporalBaseline' in product.keys() or 'perpendicularBaseline' in product.keys():
            includeBaseline = True

    template = templateEnv.get_template('template.kml')

    for line in template.stream(includeBaseline=includeBaseline, results=results_properties):
        yield line

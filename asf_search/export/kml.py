from math import floor
from asf_search.CMR import get_additional_fields
import logging
from jinja2 import Environment, PackageLoader

def get_additional_kml_fields(product):
    umm = product.umm

    extra_fields = [
        ('configurationName', ['AdditionalAttributes', ('Name', 'BEAM_MODE_DESC'), 'Values', 0]),
        ('faradayRotation', ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0]),
        ('processingTypeDisplay', ['AdditionalAttributes', ('Name', 'PROCESSING_TYPE_DISPLAY'), 'Values', 0]),
        ('sceneDate', ['AdditionalAttributes', ('Name', 'ACQUISITION_DATE'), 'Values', 0]),
        ('shape', ['SpatialExtent', 'HorizontalSpatialDomain', 'Geometry', 'GPolygons', 0, 'Boundary', 'Points']),
        ('thumbnailUrl', ['AdditionalAttributes', ('Name', 'THUMBNAIL_URL'), 'Values', 0]),
        ('faradayRotation', ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0]),
    ]

    
    additional_fields = {}
    for key, path in extra_fields:
        additional_fields[key] = get_additional_fields(umm, *path)

    return additional_fields

def ASFSearchResults_to_kml(results_properties, includeBaseline=False, addendum=None):
    logging.debug('translating: kml')

    templateEnv = Environment(
        loader=PackageLoader('asf_search.export', 'templates'),
        autoescape=True
    )

    for product in results_properties:
        if product['offNadirAngle'] != None:
            product['offNadirAngle'] = floor(product['offNadirAngle']) if product['offNadirAngle'] == floor(product['offNadirAngle']) else product['offNadirAngle']
    template = templateEnv.get_template('template.kml')

    for l in template.stream(includeBaseline=includeBaseline, results=results_properties):
        yield l

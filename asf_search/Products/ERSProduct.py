import copy
from asf_search import ASFSession, ASFProduct
from asf_search.CMR.translate import get_state_vector, get as umm_get, cast as umm_cast
from asf_search.CMR.UMMFields import float_string_as_int
from asf_search.constants import PLATFORM

class ERSProduct(ASFProduct):
    base_properties = {
        'browse': { 'path': ['RelatedUrls', ('Type', [('GET RELATED VISUALIZATION', 'URL')])]},
        'bytes': {'path': [ 'AdditionalAttributes', ('Name', 'BYTES'), 'Values', 0], 'cast': float_string_as_int},
        'frameNumber': {'path': ['AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0], 'cast': int},
        'granuleType': {'path': [ 'AdditionalAttributes', ('Name', 'GRANULE_TYPE'), 'Values', 0]},
        'insarStackId': {'path': [ 'AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0]},
        'md5sum': {'path': [ 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
        'offNadirAngle': {'path': [ 'AdditionalAttributes', ('Name', 'OFF_NADIR_ANGLE'), 'Values', 0], 'cast': float},
        'orbit': {'path': [ 'OrbitCalculatedSpatialDomains', 0, 'OrbitNumber'], 'cast': int},
        'polarization': {'path': [ 'AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values', 0]},
        'processingDate': {'path': [ 'DataGranule', 'ProductionDateTime'], },
        'sensor': {'path': [ 'Platforms', 0, 'Instruments', 0, 'ShortName'], },
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        
    @staticmethod
    def _get_property_paths() -> dict:
        return {
            **ASFProduct._get_property_paths(),
            **ERSProduct.base_properties
        }

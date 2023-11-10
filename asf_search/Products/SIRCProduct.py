import copy
from asf_search import ASFProduct, ASFSession
from asf_search.CMR.translate import get_state_vector, get as umm_get, cast as umm_cast
from asf_search.constants import PLATFORM

class SIRCProduct(ASFProduct):
    base_properties = {
        'frameNumber': {'path': ['AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0], 'cast': int},
        'polarization': {'path': [ 'AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values', 0]},
        'granuleType': {'path': [ 'AdditionalAttributes', ('Name', 'GRANULE_TYPE'), 'Values', 0]},
        'groupID': {'path': [ 'AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0]},
        'md5sum': {'path': [ 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
        'orbit': {'path': [ 'OrbitCalculatedSpatialDomains', 0, 'OrbitNumber'], 'cast': int},
        'pgeVersion': {'path': ['PGEVersionClass', 'PGEVersion'] },
        'processingDate': {'path': [ 'DataGranule', 'ProductionDateTime']},
        'sensor': {'path': [ 'Platforms', 0, 'Instruments', 0, 'ShortName']},
        'beamModeType': {'path': ['AdditionalAttributes', ('Name', 'BEAM_MODE_TYPE'), 'Values', 0]},
        'frameNumber': {'path': ['AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0], 'cast': int},
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

    @staticmethod
    def _get_property_paths() -> dict:
        return {
            **ASFProduct._get_property_paths(),
            **SIRCProduct.base_properties
        }

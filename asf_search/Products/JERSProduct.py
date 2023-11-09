import copy
from asf_search import ASFSession, ASFProduct
from asf_search.CMR.translate import get_state_vector, get as umm_get, cast as umm_cast
from asf_search.CMR.UMMFields import umm_property_paths
from asf_search.constants import PLATFORM

class JERSProduct(ASFProduct):
    base_properties = {
        'browse',
        'bytes',
        'frameNumber',
        'granuleType',
        'insarStackId',
        'md5sum',
        'offNadirAngle',
        'orbit',
        'polarization',
        'processingDate',
        'sensor'
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        
    @staticmethod
    def _get_property_paths() -> dict:
        return {
            **ASFProduct._get_property_paths(),
            **{
                prop: umm_path 
                for prop in JERSProduct.base_properties 
                if (umm_path := umm_property_paths.get(prop)) is not None
            },
        }
    
    @staticmethod
    def is_valid_product(item: dict):
        platform: str = ASFProduct.get_platform(item).lower()

        return platform in ['jers-1']
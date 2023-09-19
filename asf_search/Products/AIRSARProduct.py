import copy
from asf_search import ASFProduct, ASFSession, ASFSearchOptions
from asf_search.CMR import umm_property_paths
from asf_search.CMR.translate import get as umm_get, cast as umm_cast
from asf_search.exceptions import ASFBaselineError

class AIRSARProduct(ASFProduct):
    base_properties = {
        'bytes',
        'frameNumber',
        'granuleType',
        'groupID',
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
                for prop in AIRSARProduct.base_properties 
                if (umm_path := umm_property_paths.get(prop)) is not None
            },
        }
    
    
    @staticmethod
    def is_valid_product(item: dict):
        return AIRSARProduct.get_platform(item).lower() == 'airsar'
    

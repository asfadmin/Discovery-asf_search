import copy
from typing import Dict
from asf_search import ASFProduct, ASFSession
from asf_search.CMR.translate import try_parse_float

class UAVSARProduct(ASFProduct):
    """
    ASF Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/uavsar/
    """
    _base_properties = {
        'groupID': {'path': [ 'AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0]},
        'insarStackId': {'path': [ 'AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0]},
        'md5sum': {'path': [ 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

    @staticmethod
    def get_property_paths() -> Dict:
        return {
            **ASFProduct.get_property_paths(),
            **UAVSARProduct._base_properties
        }

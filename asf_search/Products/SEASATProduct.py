from typing import Dict
from asf_search import ASFSession, ASFProduct
from asf_search.CMR.translate import try_parse_float, try_round_float


class SEASATProduct(ASFProduct):
    """
    ASF Dataset Documentation Page: https://asf.alaska.edu/data-sets/sar-data-sets/seasat/
    """
    _base_properties = {
        'bytes': {'path': [ 'AdditionalAttributes', ('Name', 'BYTES'), 'Values', 0], 'cast': try_round_float},
        'insarStackId': {'path': [ 'AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0]},
        'md5sum': {'path': [ 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

    @staticmethod
    def get_property_paths() -> Dict:
        return {
            **ASFProduct.get_property_paths(),
            **SEASATProduct._base_properties
        }

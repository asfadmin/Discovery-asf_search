import copy
from asf_search import ASFProduct, ASFSession
from asf_search.CMR.translate import try_parse_float

class SMAPProduct(ASFProduct):
    """
    ASF Dataset Documentation Page: https://asf.alaska.edu/data-sets/sar-data-sets/soil-moisture-active-passive-smap-mission/
    """
    _base_properties = {
        'groupID': {'path': [ 'AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0]},
        'insarStackId': {'path': [ 'AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0]},
        'md5sum': {'path': [ 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
        'offNadirAngle': {'path': [ 'AdditionalAttributes', ('Name', 'OFF_NADIR_ANGLE'), 'Values', 0], 'cast': try_parse_float},
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

    @staticmethod
    def get_property_paths() -> dict:
        return {
            **ASFProduct.get_property_paths(),
            **SMAPProduct._base_properties
        }

from typing import Dict
from asf_search import ASFSession, ASFProduct
from asf_search.CMR.translate import try_parse_int


class AIRSARProduct(ASFProduct):
    """
    ASF Dataset Overview Page: https://asf.alaska.edu/data-sets/sar-data-sets/airsar/
    """

    _base_properties = {
        **ASFProduct._base_properties,
        'frameNumber': {
            'path': ['AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0],
            'cast': try_parse_int,
        },
        'groupID': {'path': ['AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0]},
        'insarStackId': {'path': ['AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0]},
        'md5sum': {'path': ['AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

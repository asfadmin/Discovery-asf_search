from typing import Dict
from asf_search import ASFProduct, ASFSession


class SMAPProduct(ASFProduct):
    """
    ASF Dataset Documentation Page:
        https://asf.alaska.edu/data-sets/sar-data-sets/soil-moisture-active-passive-smap-mission/
    """

    _base_properties = {
        **ASFProduct._base_properties,
        'groupID': {'path': ['AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0]},
        'insarStackId': {'path': ['AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0]},
        'md5sum': {'path': ['AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

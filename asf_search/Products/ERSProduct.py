from typing import Dict, Union
from asf_search import ASFSession, ASFStackableProduct
from asf_search.CMR.translate import try_round_float
from asf_search.constants import PRODUCT_TYPE


class ERSProduct(ASFStackableProduct):
    """
    Used for ERS-1 and ERS-2 products

    ASF ERS-1 Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/ers-1/
    ASF ERS-2 Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/ers-2/
    """

    _base_properties = {
        **ASFStackableProduct._base_properties,
        'frameNumber': {'path': ['AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0]},
        'bytes': {
            'path': ['AdditionalAttributes', ('Name', 'BYTES'), 'Values', 0],
            'cast': try_round_float,
        },
        'esaFrame': {'path': ['AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0]},
        'md5sum': {'path': ['AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
        'beamModeType': {'path': ['AdditionalAttributes', ('Name', 'BEAM_MODE_TYPE'), 'Values', 0]},
        'insarStackId': {'path': ['AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0]},
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

    @staticmethod
    def get_default_baseline_product_type() -> Union[str, None]:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return PRODUCT_TYPE.L0

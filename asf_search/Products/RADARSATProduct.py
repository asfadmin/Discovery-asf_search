from typing import Dict, Union
from asf_search import ASFSearchOptions, ASFSession, ASFProduct, ASFStackableProduct
from asf_search.CMR.translate import try_parse_float
from asf_search.constants import PRODUCT_TYPE


class RADARSATProduct(ASFStackableProduct):
    """
    ASF Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/radarsat-1/
    """
    _base_properties = {
        'faradayRotation': {'path': ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0], 'cast': try_parse_float},
        'md5sum': {'path': ['AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
        'beamModeType': {'path': ['AdditionalAttributes', ('Name', 'BEAM_MODE_TYPE'), 'Values', 0]},
        'insarStackId': {'path': ['AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0]},
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

    @staticmethod
    def get_property_paths() -> Dict:
        return {
            **ASFStackableProduct.get_property_paths(),
            **RADARSATProduct._base_properties
        }

    @staticmethod
    def get_default_baseline_product_type() -> Union[str, None]:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return PRODUCT_TYPE.L0

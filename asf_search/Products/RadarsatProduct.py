from typing import Dict, Union
from asf_search import ASFSearchResults, ASFSession, ASFProduct, ASFStackableProduct
from asf_search.CMR.translate import try_parse_float
from asf_search.baseline.stack import offset_perpendicular_baselines
from asf_search.constants import PRODUCT_TYPE


class RadarsatProduct(ASFStackableProduct):
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
            **RadarsatProduct._base_properties
        }

    @staticmethod
    def get_default_baseline_product_type() -> Union[str, None]:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return PRODUCT_TYPE.L0

    def get_perpendicular_baseline(self, reference: ASFProduct, stack: ASFSearchResults):
        return offset_perpendicular_baselines(reference, stack)
    
    @staticmethod
    def check_reference(reference: ASFStackableProduct, stack: ASFSearchResults):
        reference, warning = ASFStackableProduct.check_reference(reference, stack)
        
        if 'insarBaseline' not in reference.baseline:
            raise ValueError('No baseline values available for precalculated dataset')

        return reference, warning

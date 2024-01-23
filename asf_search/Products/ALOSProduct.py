from typing import Dict, Union
from asf_search import ASFSearchResults, ASFSession, ASFProduct, ASFStackableProduct, ASFSearchOptions
from asf_search.CMR.translate import try_parse_float, try_parse_int, try_round_float
from asf_search.baseline.stack import offset_perpendicular_baselines
from asf_search.constants import PRODUCT_TYPE


class ALOSProduct(ASFStackableProduct):
    """
    Used for ALOS Palsar and Avnir dataset products

    ASF Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/alos-palsar/
    """
    _base_properties = {
        'frameNumber': {'path': ['AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0], 'cast': try_parse_int},
        'faradayRotation': {'path': ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0], 'cast': try_parse_float},
        'offNadirAngle': {'path': ['AdditionalAttributes', ('Name', 'OFF_NADIR_ANGLE'), 'Values', 0], 'cast': try_parse_float},
        'bytes': {'path': ['AdditionalAttributes', ('Name', 'BYTES'), 'Values', 0], 'cast': try_round_float},
        'insarStackId': {'path': ['AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0]},
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        if self.properties.get('groupID') is None:
            self.properties['groupID'] = self.properties['sceneName']

    @staticmethod
    def get_default_baseline_product_type() -> Union[str, None]:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return PRODUCT_TYPE.L1_1
    
    def get_perpendicular_baseline(self, reference: ASFProduct, stack: ASFSearchResults):
        return offset_perpendicular_baselines(reference, stack)

    @staticmethod
    def get_property_paths() -> Dict:
        return {
            **ASFStackableProduct.get_property_paths(),
            **ALOSProduct._base_properties
        }

    @staticmethod
    def check_reference(reference: ASFStackableProduct, stack: ASFSearchResults):
        reference, warning = ASFStackableProduct.check_reference(reference, stack)
        
        if 'insarBaseline' not in reference.baseline:
            raise ValueError('No baseline values available for precalculated dataset')

        return reference, warning

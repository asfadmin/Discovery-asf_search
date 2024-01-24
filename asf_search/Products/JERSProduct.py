from typing import Dict, Union
from asf_search import ASFSearchOptions, ASFSearchResults, ASFSession, ASFProduct, ASFStackableProduct
from asf_search.baseline.stack import offset_perpendicular_baselines
from asf_search.constants import PRODUCT_TYPE


class JERSProduct(ASFStackableProduct):
    """
    ASF Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/jers-1/
    """
    _base_properties = {
        'browse': {'path': ['RelatedUrls', ('Type', [('GET RELATED VISUALIZATION', 'URL')])]},
        'groupID': {'path': ['AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0]},
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

    @staticmethod
    def get_property_paths() -> Dict:
        return {
            **ASFStackableProduct.get_property_paths(),
            **JERSProduct._base_properties
        }

    def get_perpendicular_baseline(self, reference: ASFProduct, stack: ASFSearchResults):
        return offset_perpendicular_baselines(reference, stack)
    
    @staticmethod
    def check_reference(reference: ASFStackableProduct, stack: ASFSearchResults):
        reference, warning = ASFStackableProduct.check_reference(reference, stack)
        
        if 'insarBaseline' not in reference.baseline:
            raise ValueError('No baseline values available for precalculated dataset')

        return reference, warning

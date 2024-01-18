import copy
from typing import Dict, Union
from asf_search import ASFSearchOptions, ASFSession, ASFProduct
from asf_search.constants import PRODUCT_TYPE
from asf_search.exceptions import ASFBaselineError


class JERSProduct(ASFProduct):
    """
    ASF Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/jers-1/
    """
    _base_properties = {
        'browse': {'path': ['RelatedUrls', ('Type', [('GET RELATED VISUALIZATION', 'URL')])]},
        'groupID': {'path': ['AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0]},
        'insarStackId': {'path': ['AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0]},
        'md5sum': {'path': ['AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
        'beamModeType': {'path': ['AdditionalAttributes', ('Name', 'BEAM_MODE_TYPE'), 'Values', 0]}
    }

    baseline_type = ASFProduct.BaselineCalcType.PRE_CALCULATED

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        self.baseline = self.get_baseline_calc_properties()

    def get_baseline_calc_properties(self) -> Dict:
        insarBaseline = self.umm_cast(float, self.umm_get(self.umm, 'AdditionalAttributes', ('Name', 'INSAR_BASELINE'), 'Values', 0))

        if insarBaseline is None:
            return

        return {
            'insarBaseline': insarBaseline
        }

    @staticmethod
    def get_property_paths() -> Dict:
        return {
            **ASFProduct.get_property_paths(),
            **JERSProduct._base_properties
        }

    def get_stack_opts(self, opts: ASFSearchOptions = None):
        stack_opts = (ASFSearchOptions() if opts is None else copy(opts))
        stack_opts.processingLevel = self.get_default_baseline_product_type()

        if self.properties.get('insarStackId') in [None, 'NA', 0, '0']:
            raise ASFBaselineError(f'Requested reference product needs a baseline stack ID but does not have one: {self.properties["fileID"]}')

        stack_opts.insarStackId = self.properties['insarStackId']
        return stack_opts

    def is_valid_reference(self):
        # we don't stack at all if any of stack is missing insarBaseline, unlike stacking S1 products(?)
        if 'insarBaseline' not in self.baseline:
            raise ValueError('No baseline values available for precalculated dataset')

        return True

    @staticmethod
    def get_default_baseline_product_type() -> Union[str, None]:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return PRODUCT_TYPE.L0

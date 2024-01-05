import copy
from typing import Union
from asf_search import ASFSession, ASFProduct, ASFSearchOptions
from asf_search.CMR.translate import get as umm_get, cast as umm_cast, try_parse_float, try_parse_int, try_round_float
from asf_search.constants import PRODUCT_TYPE
from asf_search.exceptions import ASFBaselineError

class ALOSProduct(ASFProduct):
    """
    Used for ALOS Palsar and Avnir dataset products

    ASF Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/alos-palsar/
    """
    base_properties = {
        'frameNumber': {'path': ['AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0], 'cast': try_parse_int},
        'faradayRotation': {'path': [ 'AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0], 'cast': try_parse_float},
        'offNadirAngle': {'path': [ 'AdditionalAttributes', ('Name', 'OFF_NADIR_ANGLE'), 'Values', 0], 'cast': try_parse_float},
        'bytes': {'path': [ 'AdditionalAttributes', ('Name', 'BYTES'), 'Values', 0], 'cast': try_round_float},
        'insarStackId': {'path': [ 'AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0]},
    }

    baseline_type = ASFProduct.BaselineCalcType.PRE_CALCULATED
    
    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        self.baseline = self.get_baseline_calc_properties()

        if self.properties.get('groupID') is None:
            self.properties['groupID'] = self.properties['sceneName']
        
    def get_baseline_calc_properties(self) -> dict:
        insarBaseline = umm_cast(float, umm_get(self.umm, 'AdditionalAttributes', ('Name', 'INSAR_BASELINE'), 'Values', 0))
        
        if insarBaseline is not None:
            return {
                'insarBaseline': insarBaseline        
            }

    def get_stack_opts(self, opts: ASFSearchOptions = None):
        stack_opts = (ASFSearchOptions() if opts is None else copy(opts))
        stack_opts.processingLevel = 'L1.1'

        if self.properties.get('insarStackId') not in [None, 'NA', 0, '0']:
            stack_opts.insarStackId = self.properties['insarStackId']
            return stack_opts
        
        raise ASFBaselineError(f'Requested reference product needs a baseline stack ID but does not have one: {self.properties["fileID"]}')
        
    @staticmethod
    def _get_property_paths() -> dict:
        return {
            **ASFProduct._get_property_paths(),
            **ALOSProduct.base_properties
        }
    
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
        return PRODUCT_TYPE.L1_1
    
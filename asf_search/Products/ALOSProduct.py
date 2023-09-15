import copy
from asf_search import ASFProduct, ASFSession, ASFSearchOptions
from asf_search.CMR import umm_property_paths
from asf_search.CMR.translate import get as umm_get, cast as umm_cast
from asf_search.exceptions import ASFBaselineError

class ALOSProduct(ASFProduct):
    base_properties = {
        'faradayRotation',
        'offNadirAngle',
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        self.baseline = self.get_baseline_calc_properties()
        self.properties['frameNumber'] = umm_cast(int, umm_get(self.umm, *umm_property_paths.get('S1AlosFrameNumber')))
        
    def get_baseline_calc_properties(self) -> dict:
        insarBaseline = umm_cast(float, umm_get(self.umm, *umm_property_paths.get('insarBaseline')))
        
        if insarBaseline is not None:
            return {
                'insarBaseline': insarBaseline        
            }
        
        return None
    
    def get_stack_opts(self, reference: ASFProduct, 
        opts: ASFSearchOptions = None):

        stack_opts = (ASFSearchOptions() if opts is None else copy(opts))
        stack_opts.processingLevel = self.get_default_product_type(reference)

        if reference.properties['insarStackId'] not in [None, 'NA', 0, '0']:
            stack_opts.insarStackId = reference.properties['insarStackId']
            return stack_opts
        
        raise ASFBaselineError(f'Requested reference product needs a baseline stack ID but does not have one: {reference.properties["fileID"]}')
        
    @staticmethod
    def _get_property_paths() -> dict:
        return {
            **ASFProduct._get_property_paths(),
            **ALOSProduct.additional_properties
        }
    
    @staticmethod
    def is_valid_product(item: dict):
        return ALOSProduct.get_platform(item).lower() == 'alos'
    

    def get_default_product_type(self):
        return 'L1.1'
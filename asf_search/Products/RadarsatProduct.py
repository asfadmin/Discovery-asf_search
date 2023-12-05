import copy
from asf_search import ASFSearchOptions, ASFSession, ASFProduct
from asf_search.CMR.translate import get as umm_get, cast as umm_cast, try_parse_float, try_parse_int
from asf_search.exceptions import ASFBaselineError

class RadarsatProduct(ASFProduct):
    base_properties = {
        'faradayRotation': {'path': [ 'AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0], 'cast': try_parse_float},
        'offNadirAngle': {'path': [ 'AdditionalAttributes', ('Name', 'OFF_NADIR_ANGLE'), 'Values', 0], 'cast': try_parse_float},
        'insarStackId': {'path': [ 'AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0]},
        'processingDate': {'path': [ 'DataGranule', 'ProductionDateTime'], },
        'orbit': {'path': [ 'OrbitCalculatedSpatialDomains', 0, 'OrbitNumber'], 'cast': try_parse_int},
        'polarization': {'path': [ 'AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values', 0]},
        'md5sum': {'path': [ 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
        'sensor': {'path': [ 'Platforms', 0, 'Instruments', 0, 'ShortName'], },
        'granuleType': {'path': [ 'AdditionalAttributes', ('Name', 'GRANULE_TYPE'), 'Values', 0]},
        'frameNumber': {'path': ['AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0], 'cast': try_parse_int},
    }
    
    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        self.baseline = self.get_baseline_calc_properties()
    
    def get_baseline_calc_properties(self) -> dict:
        insarBaseline = umm_cast(float, umm_get(self.umm, 'AdditionalAttributes', ('Name', 'INSAR_BASELINE'), 'Values', 0))
        
        if insarBaseline is not None:
            return {
                'insarBaseline': insarBaseline        
            }
        
        return None

    def get_stack_opts(self, 
        opts: ASFSearchOptions = None):

        stack_opts = (ASFSearchOptions() if opts is None else copy(opts))
        stack_opts.processingLevel = RadarsatProduct.get_default_product_type()

        if self.properties.get('insarStackId') not in [None, 'NA', 0, '0']:
            stack_opts.insarStackId = self.properties['insarStackId']
            return stack_opts
        
        raise ASFBaselineError(f'Requested reference product needs a baseline stack ID but does not have one: {self.properties["fileID"]}')
    
    @staticmethod
    def _get_property_paths() -> dict:
        return {
            **ASFProduct._get_property_paths(),
            **RadarsatProduct.base_properties
        }
    
    @staticmethod
    def get_default_product_type():
        return 'L0'
    
    def is_valid_reference(self):
        # we don't stack at all if any of stack is missing insarBaseline, unlike stacking S1 products(?)
        if 'insarBaseline' not in self.baseline:
            raise ValueError('No baseline values available for precalculated dataset')
        
        return True
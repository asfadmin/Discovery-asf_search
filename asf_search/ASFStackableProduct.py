from enum import Enum
from copy import copy
from typing import Dict, Tuple, Type, Union
from asf_search import ASFSession, ASFProduct
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.baseline.stack import calculate_temporal_baselines, offset_perpendicular_baselines
from asf_search.exceptions import ASFBaselineError


class ASFStackableProduct(ASFProduct):
    """
    Used for ERS-1 and ERS-2 products

    ASF ERS-1 Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/ers-1/
    ASF ERS-2 Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/ers-2/
    """
    _base_properties = {
    }

    class BaselineCalcType(Enum):
        """
        Defines how asf-search will calculate perpendicular baseline for products of this subclass
        """
        PRE_CALCULATED = 0
        """Has pre-calculated insarBaseline value that will be used for perpendicular calculations"""
        CALCULATED = 1
        """Uses position/velocity state vectors and ascending node time for perpendicular calculations"""

    
    baseline_type = BaselineCalcType.PRE_CALCULATED
    """Determines how asf-search will attempt to stack products of this type."""
    
    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        self.baseline = self.get_baseline_calc_properties()

    def get_baseline_calc_properties(self) -> Dict:
        insarBaseline = self.umm_cast(float, self.umm_get(self.umm, 'AdditionalAttributes', ('Name', 'INSAR_BASELINE'), 'Values', 0))

        if insarBaseline is None:
            return None

        return {
            'insarBaseline': insarBaseline
        }

    def get_stack_opts(self, opts: ASFSearchOptions = None):
        stack_opts = (ASFSearchOptions() if opts is None else copy(opts))
        stack_opts.processingLevel = self.get_default_baseline_product_type()

        if self.properties.get('insarStackId') in [None, 'NA', 0, '0']:
            raise ASFBaselineError(f'Requested reference product needs a baseline stack ID but does not have one: {self.properties["fileID"]}')

        stack_opts.insarStackId = self.properties['insarStackId']
        return stack_opts

    @staticmethod
    def get_property_paths() -> Dict:
        return {
            **ASFProduct.get_property_paths(),
            **ASFStackableProduct._base_properties
        }

    @staticmethod
    def get_default_baseline_product_type() -> Union[str, None]:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return None

    def _stack_from_product(
            self,
            opts: ASFSearchOptions = None,
            ASFProductSubclass: Type[ASFProduct] = None
        ) -> ASFSearchResults:
        """
        Finds a baseline stack from a reference ASFProduct

        :param reference: Reference scene to base the stack on, and from which to calculate perpendicular/temporal baselines
        :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.
        :param ASFProductSubclass: An ASFProduct subclass constructor
        
        :return: ASFSearchResults(dict) of search results
        """

        opts = (ASFSearchOptions() if opts is None else copy(opts))

        opts.merge_args(**dict(self.get_stack_opts()))

        from asf_search import search

        stack = search(opts=opts)

        is_complete = stack.searchComplete

        if ASFProductSubclass is not None:
            self.cast_results_to_subclass(stack, ASFProductSubclass)

        stack, warnings = self._get_baseline_from_stack(stack=stack)
        stack.searchComplete = is_complete # preserve final outcome of earlier search()

        stack.sort(key=lambda product: product.properties['temporalBaseline'])

        return stack

    def _get_baseline_from_stack(self, stack: ASFSearchResults):
        reference = self
        warnings = None

        if len(stack) == 0:
            raise ValueError('No products found matching stack parameters')
        stack = [product for product in stack if not product.properties['processingLevel'].lower().startswith('metadata') and product.baseline is not None]
        reference, warnings = reference.check_reference(reference, stack)

        stack = reference.get_temporal_baseline(stack)
        stack = reference.get_perpendicular_baseline(stack)

        return ASFSearchResults(stack), warnings

    def get_temporal_baseline(self, stack: ASFSearchResults):
        return calculate_temporal_baselines(self, stack)

    def get_perpendicular_baseline(self, stack: ASFSearchResults):
        """Get Perpendicular baselines for product. Typical implementations in `ALOSProduct` and `S1Product`"""
        raise NotImplementedError(f'Method get_perpendicular_baseline() not implemented in {type(self)}, see "Product.S1Product" or "Product.ALOSProduct" for example implementations')

    @staticmethod
    def check_reference(reference: 'ASFStackableProduct', stack: ASFSearchResults) -> Tuple['ASFStackableProduct', Dict]:
        """Asserts that the product is a valid reference for the given stack for baseline calculations. The checks are:
        1. Asserts that the product is in the stack
            - if false, use the first result in the stack as the reference
        2. Calls the reference's subclass implementation of is_valid_reference()
            - if false, search the stack for the first available valid product

        param reference: The ASFStackable
        param stack:
        If any new reference is used
            
        """
        warning = None
        if reference.properties['sceneName'] not in [product.properties['sceneName'] for product in stack]: # Somehow the reference we built the stack from is missing?! Just pick one
            reference = stack[0]
            warning = {'NEW_REFERENCE': 'A new reference scene had to be selected in order to calculate baseline values.'}
        
        return reference, warning
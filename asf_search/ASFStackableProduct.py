from enum import Enum
import copy
from typing import Dict, Union
from asf_search import ASFSession, ASFProduct
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.exceptions import ASFBaselineError


class ASFStackableProduct(ASFProduct):
    """
    Used for ERS-1 and ERS-2 products

    ASF ERS-1 Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/ers-1/
    ASF ERS-2 Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/ers-2/
    """

    class BaselineCalcType(Enum):
        """
        Defines how asf-search will calculate perpendicular baseline for products of this subclass
        """

        PRE_CALCULATED = 0
        """Has pre-calculated insarBaseline value that will be used for perpendicular calculations"""  # noqa F401
        CALCULATED = 1
        """Uses position/velocity state vectors and ascending node time for perpendicular calculations"""  # noqa F401

    baseline_type = BaselineCalcType.PRE_CALCULATED
    """Determines how asf-search will attempt to stack products of this type."""

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        self.baseline = self.get_baseline_calc_properties()

    def get_baseline_calc_properties(self) -> Dict:
        insarBaseline = self.umm_cast(
            float,
            self.umm_get(
                self.umm,
                'AdditionalAttributes',
                ('Name', 'INSAR_BASELINE'),
                'Values',
                0,
            ),
        )

        if insarBaseline is None:
            return None

        return {'insarBaseline': insarBaseline}

    def get_stack_opts(self, opts: ASFSearchOptions = None):
        stack_opts = ASFSearchOptions() if opts is None else copy(opts)
        stack_opts.processingLevel = self.get_default_baseline_product_type()

        if self.properties.get('insarStackId') in [None, 'NA', 0, '0']:
            raise ASFBaselineError(
                'Requested reference product needs a baseline stack ID '
                f'but does not have one: {self.properties["fileID"]}'
            )

        stack_opts.insarStackId = self.properties['insarStackId']
        return stack_opts

    def is_valid_reference(self):
        # we don't stack at all if any of stack is missing insarBaseline,
        # unlike stacking S1 products(?)
        if 'insarBaseline' not in self.baseline:
            raise ValueError('No baseline values available for precalculated dataset')

        return True

    @staticmethod
    def get_default_baseline_product_type() -> Union[str, None]:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return None

    def has_baseline(self) -> bool:
        baseline = self.get_baseline_calc_properties()

        return baseline is not None

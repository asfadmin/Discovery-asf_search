
from copy import copy
from typing import Dict, Optional, Type
import warnings

from asf_search import ASFSession
from asf_search.ASFProduct import ASFProduct
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.Products import S1Product
from asf_search.CMR.translate import try_parse_float
from asf_search.constants import PRODUCT_TYPE, DATASET, POLARIZATION, BEAMMODE
from asf_search import ASFSearchResults

try:
    from asf_enumeration import aria_s1_gunw
except ImportError:
    aria_s1_gunw = None


class ARIAS1GUNWProduct(S1Product):
    """
    Used for ARIA S1 GUNW Products

    ASF Dataset Documentation Page:
        https://asf.alaska.edu/data-sets/derived-data-sets/sentinel-1-interferograms/
    """

    _base_properties = {
        **S1Product._base_properties,
        'perpendicularBaseline': {
            'path': [
                'AdditionalAttributes',
                ('Name', 'PERPENDICULAR_BASELINE'),
                'Values',
                0,
            ],
            'cast': try_parse_float,
        },
        'orbit': {'path': ['OrbitCalculatedSpatialDomains']},
        'inputGranules': {'path': ['InputGranules']},
        'ariaVersion': {'path': ['AdditionalAttributes', ('Name', 'VERSION'), 'Values', 0]},
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        self.properties['orbit'] = [orbit['OrbitNumber'] for orbit in self.properties['orbit']]
        
        if self.properties.get("sceneName") is None:
            self.properties["sceneName"] = self.properties["fileID"]

        urls = self.umm_get(self.umm, 'RelatedUrls', ('Type', [('USE SERVICE API', 'URL')]), 0)

        self.properties['additionalUrls'] = []
        if urls is not None:
            self.properties['url'] = urls[0]
            self.properties['fileName'] = self.properties['fileID'] + '.' + urls[0].split('.')[-1]
            self.properties['additionalUrls'] = urls[1:]

    def get_stack_opts(self, opts: Optional[ASFSearchOptions] = None) -> Optional[ASFSearchOptions]:
        """
        Build search options that can be used to find an insar stack for this product

        :return: ASFSearchOptions describing appropriate options
        for building a stack from this product
        """
        return ARIAS1GUNWProduct.get_stack_opts_for_frame(self.properties['frameNumber'], opts)


    @staticmethod
    def get_stack_opts_for_frame(frame_id: int, opts: Optional[ASFSearchOptions] = None) -> Optional[ASFSearchOptions]:
        if aria_s1_gunw is None:
            warnings.warn("Failed to import asf-enumeration package. \
                          Make sure it's installed in your current environment to perform stacking with the ARIAS1GUNWProduct type")
            return None
        stack_opts = ASFSearchOptions() if opts is None else copy(opts)
        aria_frame = aria_s1_gunw.get_frame(frame_id)
        
        # pulled from asf-enumeration package implementation
        stack_opts.dataset = DATASET.SENTINEL1
        stack_opts.platform = ['SA', 'SB', 'SC']
        stack_opts.processingLevel = PRODUCT_TYPE.SLC
        stack_opts.beamMode = BEAMMODE.IW
        stack_opts.polarization = [POLARIZATION.VV, POLARIZATION.VV_VH]
        stack_opts.flightDirection = aria_frame.flight_direction
        stack_opts.relativeOrbit = aria_frame.path
        stack_opts.intersectsWith = aria_frame.wkt

        return stack_opts

    def is_valid_reference(self):
        return False

    @staticmethod
    def get_default_baseline_product_type() -> str:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return PRODUCT_TYPE.SLC

    def stack(
        self, opts: Optional[ASFSearchOptions] = None, useSubclass: Type['ASFProduct'] = None
    ) -> ASFSearchResults:
        from asf_search.baseline import get_baseline_from_stack
        s1_products = self.get_aria_groups_for_frame(self.properties['frameNumber'])
        
        if len(s1_products) == 0:
            reference = None
        else:
            reference = s1_products[0]

        target_stack, warnings = get_baseline_from_stack(reference, s1_products)

        return target_stack

    @staticmethod
    def _is_subclass(item: Dict) -> bool:
        platform = ASFProduct.umm_get(item['umm'], 'Platforms', 0, 'ShortName')
        if platform in ['SENTINEL-1A', 'SENTINEL-1B', 'SENTINEL-1C']:
            asf_platform = ASFProduct.umm_get(
                item['umm'],
                'AdditionalAttributes',
                ('Name', 'ASF_PLATFORM'),
                'Values',
                0,
            )
            return 'Sentinel-1 Interferogram' in asf_platform

        return False

    @staticmethod
    def get_aria_groups_for_frame(frame: str) -> ASFSearchResults:
        """Returns the sentinel1 acquisitions over a given frame that overlap the aria frame with the given aria frame ID,
        filter products from groups that overlap the frame by < 90%"""
        if aria_s1_gunw is None:
            raise ImportError(
            'Could not find asf-enumeration package in current python environment. '
            '"asf-enumeration" is an optional dependency of asf-search required '
            'for stacking with the ARIAS1GUNWProduct type. '
            'Enable by including the appropriate pip or conda install. '
            'Ex: `python3 -m pip install asf-search[asf-enumeration]`'
        )
        aria_frame = aria_s1_gunw.get_frame(frame_id=int(frame))
        groups = aria_s1_gunw.get_acquisitions(aria_frame)
        output = []

        # ignore acquisition groups with 0 products
        # take the first product that has a baseline value, otherwise just take the first product in the group
        for group in groups:
            if len(group.products) == 0:
                continue
            valid = next((product for product in group.products if product.has_baseline()), group.products[0])
            output.append(valid)

        return ASFSearchResults(output)

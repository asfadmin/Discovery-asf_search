from typing import Dict
from asf_search import ASFSession
from asf_search.ASFProduct import ASFProduct
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.Products import S1Product
from asf_search.CMR.translate import try_parse_float


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

        urls = self.umm_get(self.umm, 'RelatedUrls', ('Type', [('USE SERVICE API', 'URL')]), 0)

        self.properties['additionalUrls'] = []
        if urls is not None:
            self.properties['url'] = urls[0]
            self.properties['fileName'] = self.properties['fileID'] + '.' + urls[0].split('.')[-1]
            self.properties['additionalUrls'] = urls[1:]

    def get_stack_opts(self, opts: ASFSearchOptions = None) -> ASFSearchOptions:
        """
        Build search options that can be used to find an insar stack for this product

        :return: ASFSearchOptions describing appropriate options
        for building a stack from this product
        """
        return None

    def is_valid_reference(self):
        return False

    @staticmethod
    def get_default_baseline_product_type() -> None:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return None

    @staticmethod
    def _is_subclass(item: Dict) -> bool:
        platform = ASFProduct.umm_get(item['umm'], 'Platforms', 0, 'ShortName')
        if platform in ['SENTINEL-1A', 'SENTINEL-1B']:
            asf_platform = ASFProduct.umm_get(
                item['umm'],
                'AdditionalAttributes',
                ('Name', 'ASF_PLATFORM'),
                'Values',
                0,
            )
            return 'Sentinel-1 Interferogram' in asf_platform

        return False

from typing import Dict, Tuple
from asf_search import ASFSearchOptions, ASFSession
from asf_search.CMR.translate import try_parse_date
from asf_search.Products import S1Product


class OPERAS1Product(S1Product):
    """
    ASF Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/opera/
    """
    _base_properties = {
        'centerLat': {'path': []}, # Opera products lacks these fields
        'centerLon': {'path': []},
        'frameNumber': {'path': []},
        'operaBurstID': {'path': ['AdditionalAttributes', ('Name', 'OPERA_BURST_ID'), 'Values', 0]},
        'validityStartDate': {'path': ['TemporalExtent', 'SingleDateTime'], 'cast': try_parse_date},
        'bytes': {'path': ['DataGranule', 'ArchiveAndDistributionInformation']},
        'subswath': {'path': ['AdditionalAttributes', ('Name', 'SUBSWATH_NAME'), 'Values', 0]},
        'polarization': {'path': ['AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values']} # dual polarization is in list rather than a 'VV+VH' style format
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        self.baseline = None

        self.properties['beamMode'] = self.umm_get(self.umm, 'AdditionalAttributes', ('Name', 'BEAM_MODE'), 'Values', 0)

        self.properties['additionalUrls'] = self._get_additional_urls()

        self.properties['operaBurstID'] = self.umm_get(self.umm, 'AdditionalAttributes', ('Name', 'OPERA_BURST_ID'), 'Values', 0)
        self.properties['bytes'] = {entry['Name']: {'bytes': entry['SizeInBytes'], 'format': entry['Format']} for entry in self.properties['bytes']}

        center = self.centroid()
        self.properties['centerLat'] = center.y
        self.properties['centerLon'] = center.x

        self.properties.pop('frameNumber')

        if (processingLevel := self.properties['processingLevel']) in ['RTC', 'RTC-STATIC']:
            self.properties['bistaticDelayCorrection'] = self.umm_get(self.umm, 'AdditionalAttributes', ('Name', 'BISTATIC_DELAY_CORRECTION'), 'Values', 0)
            if processingLevel == 'RTC':
                self.properties['noiseCorrection'] = self.umm_get(self.umm, 'AdditionalAttributes', ('Name', 'NOISE_CORRECTION'), 'Values', 0)
                self.properties['postProcessingFilter'] = self.umm_get(self.umm, 'AdditionalAttributes', ('Name', 'POST_PROCESSING_FILTER'), 'Values', 0)

    def get_stack_opts(self, opts: ASFSearchOptions = ASFSearchOptions()) -> ASFSearchOptions:
        return opts

    @staticmethod
    def get_property_paths() -> Dict:
        return {
            **S1Product.get_property_paths(),
            **OPERAS1Product._base_properties
        }
    
    @staticmethod
    def get_default_baseline_product_type() -> None:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return None

    def is_valid_reference(self):
        return False

    def get_stack_opts(self, opts: ASFSearchOptions = None) -> ASFSearchOptions:
        """
        Build search options that can be used to find an insar stack for this product

        :return: ASFSearchOptions describing appropriate options for building a stack from this product
        """
        return None

    def get_sort_keys(self) -> Tuple[str, str]:
        keys = super().get_sort_keys()

        if keys[0] == '':
            return (self._read_property('validityStartDate', ''), keys[1])

        return keys

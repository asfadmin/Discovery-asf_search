from typing import Dict, Tuple, Union
from asf_search import ASFSearchOptions, ASFSession, ASFStackableProduct
from asf_search.CMR.translate import try_parse_frame_coverage, try_parse_bool, try_parse_int

class NISARProduct(ASFStackableProduct):
    """
    Used for NISAR dataset products

    ASF Dataset Documentation Page: https://asf.alaska.edu/nisar/
    """
    _base_properties = {
        **ASFStackableProduct._base_properties,
        'frameNumber': {
            'path': ['AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0],
            'cast': try_parse_int,
        },  # Sentinel, ALOSm and NISAR product alt for frameNumber (ESA_FRAME)
        'pgeVersion': {'path': ['PGEVersionClass', 'PGEVersion']},
        'mainBandPolarization': {'path': ['AdditionalAttributes', ('Name', 'FREQUENCY_A_POLARIZATION'), 'Values']},
        'sideBandPolarization': {'path': ['AdditionalAttributes', ('Name', 'FREQUENCY_B_POLARIZATION'), 'Values']},
        'frameCoverage': {'path': ['AdditionalAttributes', ('Name', 'FULL_FRAME'), 'Values', 0], 'cast': try_parse_frame_coverage},
        'jointObservation': {'path': ['AdditionalAttributes', ('Name', 'JOINT_OBSERVATION'), 'Values', 0], 'cast': try_parse_bool},
        'rangeBandwidth': {'path': ['AdditionalAttributes', ('Name', 'RANGE_BANDWIDTH_CONCAT'), 'Values']},
        'productionConfiguration': {'path': ['AdditionalAttributes', ('Name', 'PRODUCTION_PIPELINE'), 'Values', 0]},
        'processingLevel': {'path': ['AdditionalAttributes', ('Name', 'PRODUCT_TYPE'), 'Values', 0]},
        'bytes': {'path': ['DataGranule', 'ArchiveAndDistributionInformation']},
        'collectionName': {'path': ["CollectionReference", "ShortName"]},
    }
    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        if self.properties.get('processingLevel') is None:
            self.properties.pop('processingLevel', None)

        self.properties['additionalUrls'] = self._get_additional_urls()
        self.properties['browse'] = [url for url in self._get_urls() if url.endswith('.png') or url.endswith('.jpg') or url.endswith('.jpeg')]
        self.properties['s3Urls'] = self._get_s3_uris()

        if self.properties.get('groupID') is None:
            self.properties['groupID'] = self.properties['sceneName']
        self.properties['bytes'] = {
            entry['Name']: {'bytes': entry['SizeInBytes'], 'format': entry['Format']}
            for entry in self.properties['bytes']
        }
        self.properties["conceptID"] = self.umm_get(self.meta, "collection-concept-id")

    @staticmethod
    def get_default_baseline_product_type() -> Union[str, None]:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return None

    def is_valid_reference(self):
        return False

    def get_stack_opts(self, opts: ASFSearchOptions = None) -> ASFSearchOptions:
        """
        Build search options that can be used to find an insar stack for this product

        :return: ASFSearchOptions describing appropriate options
        for building a stack from this product
        """
        return None

    def get_sort_keys(self) -> Tuple[str, str]:
        keys = super().get_sort_keys()

        if keys[0] == '':
            return (self._read_property('processingDate', ''), keys[1])

        return keys

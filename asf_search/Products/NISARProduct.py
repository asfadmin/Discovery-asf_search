from typing import Dict, Tuple, Union
from asf_search import ASFSearchOptions, ASFSession, ASFStackableProduct


class NISARProduct(ASFStackableProduct):
    """
    Used for NISAR dataset products

    ASF Dataset Documentation Page: https://asf.alaska.edu/nisar/
    """

    _base_properties = {
        **ASFStackableProduct._base_properties,
        'pgeVersion': {'path': ['PGEVersionClass', 'PGEVersion']},
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        self.properties['additionalUrls'] = self._get_additional_urls()
        self.properties['s3Urls'] = self._get_s3_urls()

        if self.properties.get('groupID') is None:
            self.properties['groupID'] = self.properties['sceneName']

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

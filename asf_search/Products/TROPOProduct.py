from asf_search.ASFProduct import ASFProduct
from asf_search import ASFSession
from asf_search.constants import PRODUCT_TYPE


class TROPOProduct(ASFProduct):
    """
    S1Product Subclass made specifically for Sentinel-1 SLC-BURST products

    Key features/properties:
    - `properties['burst']` contains SLC-BURST Specific fields
        such as `fullBurstID` and `burstIndex`
    - `properties['additionalUrls']` contains BURST-XML url
    - SLC-BURST specific stacking params

    ASF Dataset Documentation Page:
        https://asf.alaska.edu/datasets/data-sets/derived-data-sets/sentinel-1-bursts/
    """

    _base_properties = {
        **ASFProduct._base_properties,
        'processingLevel': {'path': ['AdditionalAttributes', ('Name', 'PRODUCT_TYPE'),  'Values', 0]},
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        if self.properties['processingLevel'] == PRODUCT_TYPE.TROPO_ZENITH:
            
            self.umm_get(
            self.umm, "AdditionalAttributes", ("Name", 'PRODUCT_VERSION'), 'values'
            )

        self.properties['additionalUrls'] = self._get_additional_urls()
        self.properties['s3Urls'] = self._get_s3_uris()
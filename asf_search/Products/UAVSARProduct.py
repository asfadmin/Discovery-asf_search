from typing import Dict
from asf_search import ASFProduct, ASFSession


class UAVSARProduct(ASFProduct):
    """
    ASF Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/uavsar/
    """

    _base_properties = {
        **ASFProduct._base_properties,
        "groupID": {"path": ["AdditionalAttributes", ("Name", "GROUP_ID"), "Values", 0]},
        "insarStackId": {"path": ["AdditionalAttributes", ("Name", "INSAR_STACK_ID"), "Values", 0]},
        "md5sum": {"path": ["AdditionalAttributes", ("Name", "MD5SUM"), "Values", 0]},
        "processingLevel": {
            "path": ["AdditionalAttributes", ("Name", "PRODUCT_TYPE"), "Values", 0]
        },
        "polarization": {
            "path": ["AdditionalAttributes", ("Name", "POLARIZATION"), "Values"]
        },  # for consolidated collection
        "bytes": {"path": ["DataGranule", "ArchiveAndDistributionInformation"]},
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        if self.properties["bytes"] is None:
            self.properties["bytes"], self.properties["md5sum"] = self._get_file_sizes_and_sums()

            self.properties["additionalUrls"] = [
                url for url in self._get_additional_urls() if not url.endswith("-END")
            ]
            self.properties["browse"] = [
                url
                for url in self._get_urls()
                if url.endswith(".png")
                or url.endswith(".jpg")
                or url.endswith(".jpeg")
                or url.endswith(".gif")
            ]

            self.properties["s3Urls"] = self._get_s3_uris()

            self.properties["conceptID"] = self.umm_get(self.meta, "collection-concept-id")

            center = self.centroid()
            self.properties["centerLat"] = center.y
            self.properties["centerLon"] = center.x

            self.properties["platform"] = "UAVSAR"

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

    _default_browse_extensions = (".png", ".jpg", ".jpeg", ".gif")

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        if self.properties["bytes"] is None:
            self._set_additional_metadata()
            self.properties["platform"] = "UAVSAR"

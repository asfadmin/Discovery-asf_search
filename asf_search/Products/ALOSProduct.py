from typing import Dict, Union, Literal
from asf_search import ASFSession, ASFStackableProduct
from asf_search.CMR.translate import try_parse_float, try_parse_int, try_round_float
from asf_search.constants import PRODUCT_TYPE


class ALOSProduct(ASFStackableProduct):
    """
    Used for ALOS Palsar and Avnir dataset products

    ASF Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/alos-palsar/
    """

    _base_properties = {
        **ASFStackableProduct._base_properties,
        "frameNumber": {
            "path": ["AdditionalAttributes", ("Name", "FRAME_NUMBER"), "Values", 0],
            "cast": try_parse_int,
        },
        "faradayRotation": {
            "path": ["AdditionalAttributes", ("Name", "FARADAY_ROTATION"), "Values", 0],
            "cast": try_parse_float,
        },
        "offNadirAngle": {
            "path": ["AdditionalAttributes", ("Name", "OFF_NADIR_ANGLE"), "Values", 0],
            "cast": try_parse_float,
        },
        "bytes": {
            "path": ["AdditionalAttributes", ("Name", "BYTES"), "Values", 0],
            "cast": try_round_float,
        },
        "insarStackId": {"path": ["AdditionalAttributes", ("Name", "INSAR_STACK_ID"), "Values", 0]},
        "beamModeType": {"path": ["AdditionalAttributes", ("Name", "BEAM_MODE"), "Values", 0]},
        "polarization": {"path": ["AdditionalAttributes", ("Name", "POLARIZATION"), "Values"]},
    }

    _file_info_size_key = "Size"
    _file_info_size_format = "SizeUnit"

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        if self.properties["bytes"] is None:
            self._set_additional_metadata()

        if (
            self.properties["polarization"] is not None
            and len(self.properties["polarization"]) == 1
        ):
            self.properties["polarization"] = self.properties["polarization"].pop()
        if self.properties.get("groupID") is None:
            self.properties["groupID"] = self.properties["sceneName"]

    @staticmethod
    def get_default_baseline_product_type() -> Union[str, None]:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return PRODUCT_TYPE.L1_1

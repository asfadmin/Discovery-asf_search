from asf_search import ASFProduct, ASFSession

class SIRCProduct(ASFProduct):
    """
    Dataset Documentation Page: https://eospso.nasa.gov/missions/spaceborne-imaging-radar-c
    """
    base_properties = {
        'groupID': {'path': [ 'AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0]},
        'md5sum': {'path': [ 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
        'pgeVersion': {'path': ['PGEVersionClass', 'PGEVersion'] },
        'beamModeType': {'path': ['AdditionalAttributes', ('Name', 'BEAM_MODE_TYPE'), 'Values', 0]},
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

    @staticmethod
    def _get_property_paths() -> dict:
        return {
            **ASFProduct._get_property_paths(),
            **SIRCProduct.base_properties
        }

from asf_search import ASFSession
from asf_search.Products import S1Product
from asf_search.CMR.translate import try_parse_float
class ARIAS1GUNWProduct(S1Product):
    """
    Used for ARIA S1 GUNW Products

    ASF Dataset Documentation Page: https://asf.alaska.edu/data-sets/derived-data-sets/sentinel-1-interferograms/
    """
    _base_properties = {
        'perpendicularBaseline': {'path': ['AdditionalAttributes', ('Name', 'PERPENDICULAR_BASELINE'), 'Values', 0], 'cast': try_parse_float},
        'orbit': {'path': ['OrbitCalculatedSpatialDomains']}
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        self.properties['orbit'] = [orbit['OrbitNumber'] for orbit in self.properties['orbit']]

        urls = self.umm_get(self.umm, 'RelatedUrls', ('Type', [('USE SERVICE API', 'URL')]), 0)
        if urls is not None:
            self.properties['url'] = urls[0]
            self.properties['fileName'] = self.properties['fileID'] + '.' + urls[0].split('.')[-1]
            self.properties['additionalUrls'] = [urls[1]]

    @staticmethod
    def get_property_paths() -> dict:
        return {
            **S1Product.get_property_paths(),
            **ARIAS1GUNWProduct._base_properties
        }
    

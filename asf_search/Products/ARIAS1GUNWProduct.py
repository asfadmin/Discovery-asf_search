from asf_search import ASFSession
from asf_search.Products import S1Product
from asf_search.CMR.translate import get, try_parse_float, try_parse_int
from asf_search.CMR.translate import get_state_vector, get as umm_get, cast as umm_cast
class ARIAS1GUNWProduct(S1Product):
    base_properties = {
        'perpendicularBaseline': {'path': ['AdditionalAttributes', ('Name', 'PERPENDICULAR_BASELINE'), 'Values', 0], 'cast': try_parse_float},
        'orbit': {'path': ['OrbitCalculatedSpatialDomains']}
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        self.properties['orbit'] = [orbit['OrbitNumber'] for orbit in self.properties['orbit']]

        urls = get(self.umm, 'RelatedUrls', ('Type', [('USE SERVICE API', 'URL')]), 0)
        if urls is not None:
            self.properties['url'] = urls[0]
            self.properties['fileName'] = self.properties['fileID'] + '.' + urls[0].split('.')[-1]
            self.properties['additionalUrls'] = [urls[1]]

    @staticmethod
    def _get_property_paths() -> dict:
        return {
            **S1Product._get_property_paths(),
            **ARIAS1GUNWProduct.base_properties
        }
    
    @staticmethod
    def get_default_product_type():
        return None

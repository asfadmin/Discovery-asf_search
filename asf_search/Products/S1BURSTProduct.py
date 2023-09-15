from asf_search import ASFSession
from asf_search.CMR import umm_property_paths
from asf_search.Products import S1Product
from asf_search.CMR.translate import get

class S1BURSTProduct(S1Product):
    base_properties = {
        'absoluteBurstID',
        'relativeBurstID',
        'fullBurstID',
        'burstIndex',
        'samplesPerBurst',
        'subswath',
        'azimuthTime',
        'azimuthAnxTime',
        'bytes',
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        self.properties['sceneName'] = self.properties['fileID']

        self.properties['burst'] = {
            'absoluteBurstID': self.properties.pop('absoluteBurstID'),
            'relativeBurstID': self.properties.pop('relativeBurstID'),
            'fullBurstID': self.properties.pop('fullBurstID'),
            'burstIndex': self.properties.pop('burstIndex'),
            'samplesPerBurst': self.properties.pop('samplesPerBurst'),
            'subswath': self.properties.pop('subswath'),
            'azimuthTime': self.properties.pop('azimuthTime'),
            'azimuthAnxTime': self.properties.pop('azimuthAnxTime')
        }

        urls = get(self.umm, 'RelatedUrls', ('Type', [('USE SERVICE API', 'URL')]), 0)
        if urls is not None:
            self.properties['url'] = urls[0]
            self.properties['fileName'] = self.properties['fileID'] + '.' + urls[0].split('.')[-1]
            self.properties['additionalUrls'] = [urls[1]]

    @staticmethod
    def _get_property_paths() -> dict:
        return {
            **S1Product._get_property_paths(),
            **{
                prop: umm_path 
                for prop in S1BURSTProduct.base_properties 
                if (umm_path := umm_property_paths.get(prop)) is not None
            },
        }
    
    def get_default_product_type(self):
        return 'BURST'

    @staticmethod
    def is_valid_product(item: dict):
        return S1BURSTProduct.get_product_type(item) == 'BURST' and S1Product.is_valid_product(item)
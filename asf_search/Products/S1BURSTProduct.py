import copy
from asf_search import ASFSearchOptions, ASFSession
from asf_search.Products import S1Product
from asf_search.CMR.translate import get, try_parse_int
from asf_search.CMR.translate import get_state_vector, get as umm_get, cast as umm_cast
class S1BURSTProduct(S1Product):
    base_properties = {
        'absoluteBurstID': {'path': ['AdditionalAttributes', ('Name', 'BURST_ID_ABSOLUTE'), 'Values', 0], 'cast': try_parse_int},
        'relativeBurstID': {'path': ['AdditionalAttributes', ('Name', 'BURST_ID_RELATIVE'), 'Values', 0], 'cast': try_parse_int},
        'fullBurstID': {'path': ['AdditionalAttributes', ('Name', 'BURST_ID_FULL'), 'Values', 0]},
        'burstIndex': {'path': ['AdditionalAttributes', ('Name', 'BURST_INDEX'), 'Values', 0], 'cast': try_parse_int},
        'samplesPerBurst': {'path': ['AdditionalAttributes', ('Name', 'SAMPLES_PER_BURST'), 'Values', 0], 'cast': try_parse_int},
        'subswath': {'path': ['AdditionalAttributes', ('Name', 'SUBSWATH_NAME'), 'Values', 0]},
        'azimuthTime': {'path': ['AdditionalAttributes', ('Name', 'AZIMUTH_TIME'), 'Values', 0]},
        'azimuthAnxTime': {'path': ['AdditionalAttributes', ('Name', 'AZIMUTH_ANX_TIME'), 'Values', 0]},
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        self.properties['sceneName'] = self.properties['fileID']
        self.properties['bytes'] = umm_get(self.umm, 'AdditionalAttributes', ('Name', 'BYTE_LENGTH'),  'Values', 0)
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

    def get_stack_opts(self, opts: ASFSearchOptions = None):
        stack_opts = (ASFSearchOptions() if opts is None else copy(opts))
        
        stack_opts.processingLevel = S1BURSTProduct.get_default_product_type()
        stack_opts.fullBurstID = self.properties['burst']['fullBurstID']
        stack_opts.polarization = [self.properties['polarization']]
        return stack_opts
    
    @staticmethod
    def _get_property_paths() -> dict:
        return {
            **S1Product._get_property_paths(),
            **S1BURSTProduct.base_properties
        }
    
    @staticmethod
    def get_default_product_type():
        return 'BURST'

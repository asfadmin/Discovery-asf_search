from asf_search import ASFSession
from asf_search.CMR.translate import get as umm_get
from asf_search.Products import S1Product
from asf_search.constants import PLATFORM

class OPERAS1Product(S1Product):
    base_properties = {
        'centerLat': {'path': []}, # Opera products lacks these fields
        'centerLon': {'path': []}, 
        'frameNumber': {'path': []}, 
        'operaBurstID': {'path': ['AdditionalAttributes', ('Name', 'OPERA_BURST_ID'), 'Values', 0]},
        'validityStartDate': {'path': ['TemporalExtent', 'SingleDateTime']},
        'bytes': {'path': ['DataGranule', 'ArchiveAndDistributionInformation']},
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        self.baseline = None
        
        self.properties['beamMode'] = umm_get(self.umm, 'AdditionalAttributes', ('Name', 'BEAM_MODE'), 'Values', 0)
        accessUrls = [*umm_get(self.umm, 'RelatedUrls', ('Type', [('GET DATA', 'URL')]), 0), *umm_get(self.umm, 'RelatedUrls', ('Type', [('EXTENDED METADATA', 'URL')]), 0)]
        self.properties['additionalUrls'] = sorted([url for url in list(set(accessUrls)) if not url.endswith('.md5') 
                                        and not url.startswith('s3://') 
                                        and not 's3credentials' in url 
                                        and not url.endswith('.png')
                                        and url != self.properties['url']])
        self.properties['polarization'] = umm_get(self.umm, 'AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values')

        self.properties['operaBurstID'] = umm_get(self.umm, 'AdditionalAttributes', ('Name', 'OPERA_BURST_ID'), 'Values', 0)
        self.properties['bytes'] = {entry['Name']: {'bytes': entry['SizeInBytes'], 'format': entry['Format']} for entry in self.properties['bytes']}
        
        self.properties.pop('centerLat')
        self.properties.pop('centerLon')
        self.properties.pop('frameNumber')

    def get_stack_opts(self):
        return {}

    @staticmethod
    def _get_property_paths() -> dict:
        return {
            **S1Product._get_property_paths(),
            **OPERAS1Product.base_properties
        }
    
    @staticmethod
    def get_default_product_type():
        return 'CSLC'
    
    def is_valid_reference(self):
        return False
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
        'bytes': {'path': ['DataGranule', 'ArchiveAndDistributionInformation']}
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        baseline = self.get_baseline_calc_properties()
        if None not in baseline['stateVectors']['positions'].values() and len(baseline['stateVectors'].items()) > 0:
            self.baseline = baseline
        
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

        # stack_opts = (ASFSearchOptions() if opts is None else copy(opts))
        return {
            'processingLevel': 'SLC',
            'beamMode': [self.properties['beamModeType']],
            'flightDirection': self.properties['flightDirection'],
            'relativeOrbit': [int(self.properties['pathNumber'])], # path
            'platform': [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B],
            'polarization': ['HH','HH+HV'] if self.properties['polarization'] in ['HH','HH+HV'] else ['VV', 'VV+VH'],
            'intersectsWith': self.centroid().wkt
        }

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
        # we don't stack at all if any of stack is missing insarBaseline, unlike stacking S1 products(?)
        if 'insarBaseline' not in self.baseline:
            raise ValueError('No baseline values available for precalculated dataset')
        
        return True
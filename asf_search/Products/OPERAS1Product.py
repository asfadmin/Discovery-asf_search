from asf_search import ASFSession
from asf_search.CMR.translate import get as umm_get
from asf_search.Products import S1Product
from asf_search.constants import PLATFORM
import re
from os.path import basename

class OPERAS1Product(S1Product):
    base_properties = {
        'centerLat': {'path': []}, # Opera products lacks these fields
        'centerLon': {'path': []}, 
        'frameNumber': {'path': []}, 
        'operaBurstID': {'path': ['AdditionalAttributes', ('Name', 'OPERA_BURST_ID'), 'Values', 0]},
        'validityStartDate': {'path': ['TemporalExtent', 'SingleDateTime']},
        'bytes': {'path': ['DataGranule', 'ArchiveAndDistributionInformation']},
    }

    opera_product_type_displays = {
        'hh': 'HH GeoTIFF',
        'hv': 'HV GeoTIFF',
        'vv': 'VV GeoTIFF',
        'vh': 'VH GeoTIFF',
        'mask': 'Mask GeoTIFF',
        'h5': 'HDF5',
        'xml': 'Metadata XML',
        'rtc_anf_gamma0_to_sigma0': 'RTC Gamma to Sigma GeoTIFF',
        'number_of_looks': '# of Looks GeoTIFF',
        'incidence_angle': 'Incidence Angle GeoTIFF',
        'rtc_anf_gamma0_to_beta0': 'RTC Gamm to Beta GeoTIFF',
        'local_incidence_angle': 'Local Incidence Angle GeoTIFF'
    }

    subproduct_regex = r'(_v[0-9]\.[0-9])(\.(([^\W_])*)|_(([^\W_]*(_*))*).)'


    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        self.baseline = None
        
        self.properties['beamMode'] = umm_get(self.umm, 'AdditionalAttributes', ('Name', 'BEAM_MODE'), 'Values', 0)
        self.properties['bytes'] = {entry['Name']: {'bytes': entry['SizeInBytes'], 'format': entry['Format']} for entry in self.properties['bytes']}
        
        accessUrls = [*umm_get(self.umm, 'RelatedUrls', ('Type', [('GET DATA', 'URL')]), 0), *umm_get(self.umm, 'RelatedUrls', ('Type', [('EXTENDED METADATA', 'URL')]), 0)]
        self.properties['additionalUrls'] = sorted([url for url in list(set(accessUrls)) if not url.endswith('.md5') 
                                        and not url.startswith('s3://') 
                                        and not 's3credentials' in url 
                                        and not url.endswith('.png')
                                        and url != self.properties['url']])
        
        self.filesByKey = self.get_opera_subproduct_metadata()

        self.properties['polarization'] = umm_get(self.umm, 'AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values')

        self.properties['operaBurstID'] = umm_get(self.umm, 'AdditionalAttributes', ('Name', 'OPERA_BURST_ID'), 'Values', 0)

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
    
    def get_sort_keys(self):
        keys = super().get_sort_keys()

        if keys[0] is None:
            keys = self.properties.get('validityStartDate'), keys[1]
        
        return keys
    
    def get_opera_subproduct_metadata(self) -> dict:
        accessUrls = [*umm_get(self.umm, 'RelatedUrls', ('Type', [('GET DATA', 'URL')]), 0), *umm_get(self.umm, 'RelatedUrls', ('Type', [('EXTENDED METADATA', 'URL')]), 0)]
        urls = sorted([url for url in list(set(accessUrls)) if not url.endswith('.md5') 
                                        and not url.startswith('s3://') 
                                        and not 's3credentials' in url 
                                        and not url.endswith('.png')
                                        and url != self.properties['url']])
        
        downloadUrl: str = self.properties['url']
        reg = re.split(self.subproduct_regex, downloadUrl)
        file_suffix = reg[3] if reg[3] is not None else reg[5]
        opera_urls = {}

        self.properties['description'] = self.opera_product_type_displays.get(file_suffix.lower(), '')

        for p in [url for url in urls if url != downloadUrl]:
            reg = re.split(self.subproduct_regex, p)
            file_suffix = reg[3] if reg[3] is not None else reg[5]

            if file_suffix == 'iso':
                file_suffix = 'xml'
            
            opera_urls[file_suffix.lower()] = {
                'url': p, 
                'fileName': (fileName := basename(p)),
                'description': self.opera_product_type_displays.get(file_suffix.lower(), ''),
                'bytes': self.properties['bytes'][fileName]['bytes']
                }
        
        return opera_urls
    
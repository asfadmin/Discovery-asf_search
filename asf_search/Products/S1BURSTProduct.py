import copy
from asf_search import ASFSearchOptions, ASFSession
from asf_search.Products import S1Product
from asf_search.CMR.translate import get, try_parse_int

class S1BURSTProduct(S1Product):
    """
    S1Product Subclass made specifically for Sentinel-1 SLC-BURST products
    
    Key features/properties:
    - `properties['burst']` contains SLC-BURST Specific fields such as `fullBurstID` and `burstIndex`
    - `properties['additionalUrls']` contains BURST-XML url
    - SLC-BURST specific stacking params

    ASF Dataset Documentation Page: https://asf.alaska.edu/datasets/data-sets/derived-data-sets/sentinel-1-bursts/
    """
    base_properties = {
        'bytes': {'path': ['AdditionalAttributes', ('Name', 'BYTE_LENGTH'),  'Values', 0]},
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

        # Gathers burst properties into `burst` specific dict 
        # rather than properties dict to limit breaking changes
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
            self.properties['additionalUrls'] = [urls[1]] # xml-metadata url

    def get_stack_opts(self, opts: ASFSearchOptions = None):
        """
        Returns the search options asf-search will use internally to build an SLC-BURST baseline stack from
        
        :param opts: additional criteria for limiting 
        :returns ASFSearchOptions used for build Sentinel-1 SLC-BURST Stack
        """
        stack_opts = (ASFSearchOptions() if opts is None else copy(opts))
        
        stack_opts.processingLevel = 'BURST'
        stack_opts.fullBurstID = self.properties['burst']['fullBurstID']
        stack_opts.polarization = [self.properties['polarization']]
        return stack_opts
    
    @staticmethod
    def _get_property_paths() -> dict:
        return {
            **S1Product._get_property_paths(),
            **S1BURSTProduct.base_properties
        }
    
    def get_additional_filenames_and_urls(self, default_filename: str = None):
        # Burst XML filenames are just numbers, this makes it more indentifiable
        if file_name is None:
            file_name = '.'.join(self.properties['fileName'].split('.')[:-1]) + 'xml'
        else:
            file_name = '.'.join(default_filename.split('.')[:-1]) + 'xml'
        
        return [(file_name, self.properties['additionalUrls'][0])]
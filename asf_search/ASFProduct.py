import os
import warnings
from shapely.geometry import shape, Point, Polygon, mapping
import json

from urllib import parse

from asf_search import ASFSession, ASFSearchResults
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.download import download_url
from remotezip import RemoteZip

from asf_search.download.file_download_type import FileDownloadType
from asf_search import ASF_LOGGER
from asf_search.CMR.translate import try_parse_float, try_parse_int, try_round_float
from asf_search.CMR.translate import get as umm_get


class ASFProduct:
    base_properties = {
            # min viable product
            'centerLat': {'path': ['AdditionalAttributes', ('Name', 'CENTER_LAT'), 'Values', 0], 'cast': try_parse_float},
            'centerLon': {'path': ['AdditionalAttributes', ('Name', 'CENTER_LON'), 'Values', 0], 'cast': try_parse_float},
            'stopTime': {'path': ['TemporalExtent', 'RangeDateTime', 'EndingDateTime']}, # primary search results sort key
            'fileID': {'path': ['GranuleUR']}, # secondary search results sort key
            'flightDirection': {'path': [ 'AdditionalAttributes', ('Name', 'ASCENDING_DESCENDING'), 'Values', 0]},
            'pathNumber': {'path': ['AdditionalAttributes', ('Name', 'PATH_NUMBER'), 'Values', 0], 'cast': try_parse_int},
            'processingLevel': {'path': [ 'AdditionalAttributes', ('Name', 'PROCESSING_TYPE'), 'Values', 0]},
            
            # commonly used
            'url': {'path': [ 'RelatedUrls', ('Type', 'GET DATA'), 'URL']},
            'startTime': {'path': [ 'TemporalExtent', 'RangeDateTime', 'BeginningDateTime']},
            'sceneName': {'path': [ 'DataGranule', 'Identifiers', ('IdentifierType', 'ProducerGranuleId'), 'Identifier']},
            'browse': {'path': ['RelatedUrls', ('Type', [('GET RELATED VISUALIZATION', 'URL')])]},
            'platform': {'path': [ 'AdditionalAttributes', ('Name', 'ASF_PLATFORM'), 'Values', 0]},
            'bytes': {'path': [ 'AdditionalAttributes', ('Name', 'BYTES'), 'Values', 0], 'cast': try_round_float},
            'md5sum': {'path': [ 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
            'frameNumber': {'path': ['AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0], 'cast': try_parse_int}, # overloaded by S1, ALOS, and ERS
            'granuleType': {'path': [ 'AdditionalAttributes', ('Name', 'GRANULE_TYPE'), 'Values', 0]},
            'orbit': {'path': [ 'OrbitCalculatedSpatialDomains', 0, 'OrbitNumber'], 'cast': try_parse_int},
            'polarization': {'path': [ 'AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values', 0]},
            'processingDate': {'path': [ 'DataGranule', 'ProductionDateTime'], },
            'sensor': {'path': [ 'Platforms', 0, 'Instruments', 0, 'ShortName'], },
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        self.meta = args.get('meta')
        self.umm = args.get('umm')

        translated = self.translate_product(args)

        self.properties = translated['properties']
        self.geometry = translated['geometry']
        self.baseline = None
        self.session = session


    def __str__(self):
        return json.dumps(self.geojson(), indent=2, sort_keys=True)

    def geojson(self) -> dict:
        return {
            'type': 'Feature',
            'geometry': self.geometry,
            'properties': self.properties
        }

    def download(self, path: str, filename: str = None, session: ASFSession = None, fileType = FileDownloadType.DEFAULT_FILE) -> None:
        """
        Downloads this product to the specified path and optional filename.

        :param path: The directory into which this product should be downloaded.
        :param filename: Optional filename to use instead of the original filename of this product.
        :param session: The session to use, defaults to the one used to find the results.

        :return: None
        """

        default_filename = self.properties['fileName']

        if filename is not None:
            multiple_files = (
                (fileType == FileDownloadType.ADDITIONAL_FILES and len(self.properties['additionalUrls']) > 1) 
                or fileType == FileDownloadType.ALL_FILES
            )
            if multiple_files:
                warnings.warn(f"Attempting to download multiple files for product, ignoring user provided filename argument \"{filename}\", using default.")
            else:
                default_filename = filename
                
        if session is None:
            session = self.session

        urls = []

        def get_additional_urls():
            output = []
            for url in self.properties['additionalUrls']:
                if self.properties['processingLevel'] == 'BURST':
                    # Burst XML filenames are just numbers, this makes it more indentifiable
                    file_name = '.'.join(default_filename.split('.')[:-1]) + url.split('.')[-1]
                else:
                    # otherwise just use the name found in the url
                    file_name = os.path.split(parse.urlparse(url).path)[1]
                urls.append((f"{file_name}", url))
            
            return output

        if fileType == FileDownloadType.DEFAULT_FILE:
            urls.append((default_filename, self.properties['url']))
        elif fileType == FileDownloadType.ADDITIONAL_FILES:
            urls.extend(get_additional_urls())
        elif fileType == FileDownloadType.ALL_FILES:
            urls.append((default_filename, self.properties['url']))
            urls.extend(get_additional_urls())
        else:
            raise ValueError("Invalid FileDownloadType provided, the valid types are 'DEFAULT_FILE', 'ADDITIONAL_FILES', and 'ALL_FILES'")

        for filename, url in urls:
            download_url(url=url, path=path, filename=filename, session=session)

    def stack(
            self,
            opts: ASFSearchOptions = None
    ) -> ASFSearchResults:
        """
        Builds a baseline stack from this product.

        :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.

        :return: ASFSearchResults containing the stack, with the addition of baseline values (temporal, perpendicular) attached to each ASFProduct.
        """
        from .search.baseline_search import stack_from_product

        if opts is None:
            opts = ASFSearchOptions(session=self.session)

        return stack_from_product(self, opts=opts)

    def get_stack_opts(self) -> ASFSearchOptions:
        """
        Build search options that can be used to find an insar stack for this product

        :return: ASFSearchOptions describing appropriate options for building a stack from this product
        """
        return {}

    def centroid(self) -> Point:
        """
        Finds the centroid of a product
        """
        coords = mapping(shape(self.geometry))['coordinates'][0]
        lons = [p[0] for p in coords]
        if max(lons) - min(lons) > 180:
            unwrapped_coords = [a if a[0] > 0 else [a[0] + 360, a[1]] for a in coords]
        else:
            unwrapped_coords = [a for a in coords]

        return Polygon(unwrapped_coords).centroid

    def remotezip(self, session: ASFSession) -> RemoteZip:
        """Returns a RemoteZip object which can be used to download a part of an ASFProduct's zip archive.
        (See example in examples/5-Download.ipynb)
        
        :param session: an authenticated ASFSession
        """
        from .download.download import remotezip

        return remotezip(self.properties['url'], session=session)

    def translate_product(self, item: dict) -> dict:
        try:
            coordinates = item['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']['GPolygons'][0]['Boundary']['Points']
            coordinates = [[c['Longitude'], c['Latitude']] for c in coordinates]
            geometry = {'coordinates': [coordinates], 'type': 'Polygon'}
        except KeyError:
            geometry = {'coordinates': None, 'type': 'Polygon'}

        umm = item.get('umm')

        properties = {
            prop: umm_entry['cast'](umm_get(umm, *umm_entry['path'])) if umm_entry.get('cast') is not None else umm_get(umm, *umm_entry['path'])
            for prop, umm_entry in self._get_property_paths().items()
        }

        if properties.get('url') is not None:
            properties['fileName'] = properties['url'].split('/')[-1]
        else:
            properties['fileName'] = None

        # Fallbacks
        if properties.get('beamModeType') is None:
            properties['beamModeType'] = umm_get(umm, 'AdditionalAttributes', ('Name', 'BEAM_MODE'), 'Values', 0)
        
        if properties.get('platform') is None:
            properties['platform'] = umm_get(umm, 'Platforms', 0, 'ShortName')

        return {'geometry': geometry, 'properties': properties, 'type': 'Feature'}

    # ASFProduct subclasses define extra/override param key + UMM pathing here 
    @staticmethod
    def _get_property_paths() -> dict:
        return ASFProduct.base_properties
    
    def get_baseline_calc_properties(self) -> dict:
        return {}
    
    @staticmethod
    def get_default_product_type():
        return None

    def is_valid_reference(self):
        return False
    
    def get_sort_keys(self):
        return (self.properties.get('stopTime'), self.properties.get('fileID', 'sceneName'))
    
import os
from typing import Any, Dict, Tuple, Type, List, final
import warnings
from shapely.geometry import shape, Point, Polygon, mapping
import json

from urllib import parse

from asf_search import ASFSession, ASFSearchResults
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.download import download_url
from asf_search.download.file_download_type import FileDownloadType
from asf_search.CMR.translate import try_parse_date
from asf_search.CMR.translate import try_parse_float, try_parse_int, try_round_float


class ASFProduct:
    """
    The ASFProduct class is the base class for search results from asf-search.
    Key props:
        - properties:
            - stores commonly acessed properties of the CMR UMM for convenience
        - umm:
            - The data portion of the CMR response
        - meta:
            - The metadata portion of the CMR response
        - geometry:
            - The geometry `{coordinates: [[lon, lat] ...], 'type': Polygon}`
        - baseline:
            - used for spatio-temporal baseline stacking, stores state vectors/ascending
                node time/insar baseline values when available (Not set in base ASFProduct class)
            - See `S1Product` or `ALOSProduct` `get_baseline_calc_properties()`
                methods for implementation examples

    Key methods:
        - `download()`
        - `stack()`
        - `remotezip()`


    """

    @classmethod
    def get_classname(cls):
        return cls.__name__

    _base_properties = {
        # min viable product
        'centerLat': {
            'path': ['AdditionalAttributes', ('Name', 'CENTER_LAT'), 'Values', 0],
            'cast': try_parse_float,
        },
        'centerLon': {
            'path': ['AdditionalAttributes', ('Name', 'CENTER_LON'), 'Values', 0],
            'cast': try_parse_float,
        },
        'stopTime': {
            'path': ['TemporalExtent', 'RangeDateTime', 'EndingDateTime'],
            'cast': try_parse_date,
        },  # primary search results sort key
        'fileID': {'path': ['GranuleUR']},  # secondary search results sort key
        'flightDirection': {
            'path': [
                'AdditionalAttributes',
                ('Name', 'ASCENDING_DESCENDING'),
                'Values',
                0,
            ]
        },
        'pathNumber': {
            'path': ['AdditionalAttributes', ('Name', 'PATH_NUMBER'), 'Values', 0],
            'cast': try_parse_int,
        },
        'processingLevel': {
            'path': ['AdditionalAttributes', ('Name', 'PROCESSING_TYPE'), 'Values', 0]
        },
        # commonly used
        'url': {'path': ['RelatedUrls', ('Type', 'GET DATA'), 'URL']},
        'startTime': {
            'path': ['TemporalExtent', 'RangeDateTime', 'BeginningDateTime'],
            'cast': try_parse_date,
        },
        'sceneName': {
            'path': [
                'DataGranule',
                'Identifiers',
                ('IdentifierType', 'ProducerGranuleId'),
                'Identifier',
            ]
        },
        'browse': {'path': ['RelatedUrls', ('Type', [('GET RELATED VISUALIZATION', 'URL')])]},
        'platform': {'path': ['AdditionalAttributes', ('Name', 'ASF_PLATFORM'), 'Values', 0]},
        'bytes': {
            'path': ['AdditionalAttributes', ('Name', 'BYTES'), 'Values', 0],
            'cast': try_round_float,
        },
        'md5sum': {'path': ['AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
        'frameNumber': {
            'path': ['AdditionalAttributes', ('Name', 'CENTER_ESA_FRAME'), 'Values', 0],
            'cast': try_parse_int,
        },  # overloaded by S1, ALOS, and ERS
        'granuleType': {'path': ['AdditionalAttributes', ('Name', 'GRANULE_TYPE'), 'Values', 0]},
        'orbit': {
            'path': ['OrbitCalculatedSpatialDomains', 0, 'OrbitNumber'],
            'cast': try_parse_int,
        },
        'polarization': {'path': ['AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values', 0]},
        'processingDate': {
            'path': ['DataGranule', 'ProductionDateTime'],
            'cast': try_parse_date,
        },
        'sensor': {
            'path': ['Platforms', 0, 'Instruments', 0, 'ShortName'],
        },
    }
    """
    _base_properties dictionary, mapping readable property names to paths and optional type casting

    entries are organized as such:
        - `PROPERTY_NAME`: The name the property should be called in `ASFProduct.properties`
            - `path`: the expected path in the CMR UMM json granule response as a list
            - `cast`: (optional): the optional type casting method

<<<<<<< HEAD
    Defining `_base_properties` in subclasses allows for
    defining custom properties or overiding existing ones.
    See `S1Product.get_property_paths()` on how subclasses are expected to
    combine `ASFProduct._base_properties` with their own separately defined `_base_properties`
=======
    Defining `_properties_paths` in subclasses allows for defining custom properties or overiding existing ones.
>>>>>>> master
    """

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        self.meta = args.get('meta')
        self.umm = args.get('umm')

        translated = self.translate_product(args)

        self.properties = translated['properties']
        self.geometry = translated['geometry']
        self.baseline = None
        self.session = session

    def __str__(self):
        return json.dumps(self.geojson(), indent=2, sort_keys=True)

    def geojson(self) -> Dict:
        """
        Returns ASFProduct object as a geojson formatted dictionary
        with `type`, `geometry`, and `properties` keys
        """
        return {
            'type': 'Feature',
            'geometry': self.geometry,
            'properties': self.properties,
        }

    def download(
        self,
        path: str,
        filename: str = None,
        session: ASFSession = None,
        fileType=FileDownloadType.DEFAULT_FILE,
    ) -> None:
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
                fileType == FileDownloadType.ADDITIONAL_FILES
                and len(self.properties['additionalUrls']) > 1
            ) or fileType == FileDownloadType.ALL_FILES
            if multiple_files:
                warnings.warn(
                    'Attempting to download multiple files for product, '
                    f'ignoring user provided filename argument "{filename}", using default.'
                )
            else:
                default_filename = filename

        if session is None:
            session = self.session

        urls = self.get_urls(fileType=fileType)

        for url in urls:
            base_filename = '.'.join(default_filename.split('.')[:-1])
            extension = url.split('.')[-1]
            download_url(
                url=url,
                path=path,
                filename=f'{base_filename}.{extension}',
                session=session,
            )

    def get_urls(self, fileType=FileDownloadType.DEFAULT_FILE) -> list:
        urls = []

        if fileType == FileDownloadType.DEFAULT_FILE:
            urls.append(self.properties['url'])
        elif fileType == FileDownloadType.ADDITIONAL_FILES:
            urls.extend(self.properties.get('additionalUrls', []))
        elif fileType == FileDownloadType.ALL_FILES:
            urls.append(self.properties['url'])
            urls.extend(self.properties.get('additionalUrls', []))
        else:
            raise ValueError(
                "Invalid FileDownloadType provided, the valid types are 'DEFAULT_FILE', 'ADDITIONAL_FILES', and 'ALL_FILES'"
            )
        return urls

    def _get_additional_filenames_and_urls(
        self,
        default_filename: str = None,  # for subclasses without fileName in url (see S1BurstProduct implementation) # noqa F401
    ) -> List[Tuple[str, str]]:
        return [
            (self._parse_filename_from_url(url), url)
            for url in self.properties.get('additionalUrls', [])
        ]

    def _parse_filename_from_url(self, url: str) -> str:
        file_path = os.path.split(parse.urlparse(url).path)
        filename = file_path[1]
        return filename

    def stack(
        self, opts: ASFSearchOptions = None, useSubclass: Type['ASFProduct'] = None
    ) -> ASFSearchResults:
        """
        Builds a baseline stack from this product.
        Parameters
        ----------
        opts:
        An ASFSearchOptions object describing the search parameters to be used.
        Search parameters specified outside this object will override in event of a conflict.
        ASFProductSubclass: An ASFProduct subclass constructor to cast results to

        Returns
        ----------
        asf_search.ASFSearchResults
            containing the stack, with the addition of baseline values
            (temporal, perpendicular) attached to each ASFProduct.
        """
        from .search.baseline_search import stack_from_product

        if opts is None:
            opts = ASFSearchOptions(session=self.session)

        return stack_from_product(self, opts=opts, ASFProductSubclass=useSubclass)

    def get_stack_opts(self, opts: ASFSearchOptions = None) -> ASFSearchOptions:
        """
        Build search options that can be used to find an insar stack for this product

        :return: ASFSearchOptions describing appropriate options
        for building a stack from this product
        """
        return None

    def _get_access_urls(
        self, url_types: List[str] = ['GET DATA', 'EXTENDED METADATA']
    ) -> List[str]:
        accessUrls = []

        for url_type in url_types:
            if urls := self.umm_get(self.umm, 'RelatedUrls', ('Type', [(url_type, 'URL')]), 0):
                accessUrls.extend(urls)

        return sorted(list(set(accessUrls)))

    def _get_additional_urls(self) -> List[str]:
        accessUrls = self._get_access_urls(['GET DATA', 'EXTENDED METADATA'])
        return [
            url
            for url in accessUrls
            if not url.endswith('.md5')
            and not url.startswith('s3://')
            and 's3credentials' not in url
            and not url.endswith('.png')
            and url != self.properties['url']
        ]

    def _get_s3_urls(self) -> List[str]:
        s3_urls = self._get_access_urls(
            ['GET DATA', 'EXTENDED METADATA', 'GET DATA VIA DIRECT ACCESS']
        )
        return [url for url in s3_urls if url.startswith('s3://')]

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

    def remotezip(self, session: ASFSession) -> 'RemoteZip':  # type: ignore # noqa: F821
        """Returns a RemoteZip object which can be used to download
        a part of an ASFProduct's zip archive. (See example in examples/5-Download.ipynb)

        requires installing optional dependencies via pip or conda to use the `remotezip` package:

        `python3 -m pip install asf-search[extras]`

        :param session: an authenticated ASFSession
        """
        from .download.download import remotezip

        return remotezip(self.properties['url'], session=session)

    def _read_umm_property(self, umm: Dict, mapping: Dict) -> Any:
        value = self.umm_get(umm, *mapping['path'])
        if mapping.get('cast') is None:
            return value

        return self.umm_cast(mapping['cast'], value)

    def translate_product(self, item: Dict) -> Dict:
        """
        Generates `properties` and `geometry` from the CMR UMM response
        """
        try:
            coordinates = item['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry'][
                'GPolygons'
            ][0]['Boundary']['Points']
            coordinates = [[c['Longitude'], c['Latitude']] for c in coordinates]
            geometry = {'coordinates': [coordinates], 'type': 'Polygon'}
        except KeyError:
            geometry = {'coordinates': None, 'type': 'Polygon'}

        umm = item.get('umm')

        # additionalAttributes = {attr['Name']: attr['Values'] for attr in umm['AdditionalAttributes']}

        properties = {
            prop: self._read_umm_property(umm, umm_mapping)
            for prop, umm_mapping in self._base_properties.items()
        }

        if properties.get('url') is not None:
            properties['fileName'] = properties['url'].split('/')[-1]
        else:
            properties['fileName'] = None

        # Fallbacks
        if properties.get('beamModeType') is None:
            properties['beamModeType'] = self.umm_get(
                umm, 'AdditionalAttributes', ('Name', 'BEAM_MODE'), 'Values', 0
            )

        if properties.get('platform') is None:
            properties['platform'] = self.umm_get(umm, 'Platforms', 0, 'ShortName')

        return {'geometry': geometry, 'properties': properties, 'type': 'Feature'}

    def get_sort_keys(self) -> Tuple[str, str]:
        """
        Returns tuple of primary and secondary date values used for sorting final search results
        Any subclasses must return string for final `sort()` to work
        """
        # `sort()` will raise an error when comparing `NoneType`,
        # using self._read_property() to wrap standard `dict.get()` for possible `None` values
        primary_key = self._read_property(key='stopTime', default='')
        secondary_key = self._read_property(
            key='fileID', default=self._read_property('sceneName', '')
        )

        return (primary_key, secondary_key)

    def _read_property(self, key: str, default: Any = None) -> Any:
        """
        Helper method wraps `properties.get()`.
        Since a property can be `None`, if the key exists`dict.get('key', 'default')`
        will never return the default
        """
        output = default
        if (value := self.properties.get(key)) is not None:
            output = value

        return output

    @final
    @staticmethod
    def umm_get(item: Dict, *args):
        """
        Used to search for values in CMR UMM

        :param item: the umm dict returned from CMR
        :param *args: the expected path to the value

        Example case:
        "I want to grab the polarization from the granule umm"
        ```
        item = {
            'AdditionalAttributes': [
                {
                    'Name': 'POLARIZATION',
                    'Values': ['VV', 'VH']
                },
                ...
            ],
            ...
        }
        ```

        The path provided to *args would look like this:
        ```
        'AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values', 0
        result: 'VV'
        ```

        - `'AdditionalAttributes'` acts like item['AdditionalAttributes'],
        which is a list of dictionaries

        - Since `AdditionalAttributes` is a LIST of dictionaries,
        we search for a dict with the key value pair,
        `('Name', 'POLARIZATION')`

        - If found, we try to access that dictionary's `Values` key
        - Since `Values` is a list, we can access the first index `0` (in this case, 'VV')

        ---

        If you want more of the umm, simply reduce how deep you search:
        Example: "I need BOTH polarizations (`OPERAS1Product` does this, noticed the omitted `0`)

        ```
        'AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values'
        result: ['VV', 'VH']
        ```

        ---

        Example: "I need the ENTIRE POLARIZATION dict"

        ```
        'AdditionalAttributes', ('Name', 'POLARIZATION')
        result: {
                    'Name': 'POLARIZATION',
                    'Values': ['VV', 'VH']
                }
        ```

        ---

        ADVANCED:
        Sometimes there are multiple dictionaries in a list that have
        the same key value pair we're searching for (See `OPERAS1Product` umm under `RelatedUrls`).
        This means we can miss values since we're only grabbing the first match
        depending on how the umm is organized.
        There is a way to get ALL data that matches our key value criteria.

        Example: "I need ALL `URL` values for dictionaries in `RelatedUrls`
        where `Type` is `GET DATA`" (See in use in `OPERAS1Product` class)
        ```
        'RelatedUrls', ('Type', [('GET DATA', 'URL')]), 0
        ```
        """
        if item is None:
            return None
        for key in args:
            if isinstance(key, str):
                item = item.get(key)
            elif isinstance(key, int):
                item = item[key] if key < len(item) else None
            elif isinstance(key, tuple):
                (a, b) = key
                if isinstance(b, List):
                    output = []
                    b = b[0]
                    for child in item:
                        if ASFProduct.umm_get(child, key[0]) == b[0]:
                            output.append(ASFProduct.umm_get(child, b[1]))
                    if len(output):
                        return output

                    return None

                found = False
                for child in item:
                    if ASFProduct.umm_get(child, a) == b:
                        item = child
                        found = True
                        break
                if not found:
                    return None
            if item is None:
                return None
        if item in [None, 'NA', 'N/A', '']:
            item = None
        return item

    @final
    @staticmethod
    def umm_cast(f, v):
        """Tries to cast value v by callable f, returns None if it fails"""
        try:
            return f(v)
        except TypeError:
            return None

    @staticmethod
    def _is_subclass(item: Dict) -> bool:
        """
        Used to determine which subclass to use for specific
        edge-cases when parsing results in search methods
        (Currently implemented for ARIA and OPERA subclasses).

        params:
        - item (dict): the CMR UMM-G item to read from
        """
        raise NotImplementedError()

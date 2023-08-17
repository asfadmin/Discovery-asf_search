import warnings
from shapely.geometry import shape, Point, Polygon, mapping
import json

from asf_search import ASFSession, ASFSearchResults
from asf_search.ASFSearchOptions import ASFSearchOptions 
from asf_search.download import download_url
from asf_search.CMR import translate_product
from remotezip import RemoteZip

from asf_search.download.file_download_type import FileDownloadType
from asf_search import ASF_LOGGER


class ASFProduct:
    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        self.meta = args.get('meta')
        self.umm = args.get('umm')

        translated = translate_product(args)

        self.properties = translated['properties']
        self.geometry = translated['geometry']
        self.baseline = translated['baseline']
        self.session = session

        if 'additionalUrls' not in self.properties or len(self.properties['additionalUrls']) == 0:
            self.multiple_files = False
        else:
            self.multiple_files = True

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
            # Check if we should support the filename argument:
            if self.multiple_files and fileType in [FileDownloadType.ADDITIONAL_FILES, FileDownloadType.ALL_FILES]:
                warnings.warn(f"Attempting to download multiple files for product, ignoring user provided filename argument '{filename}', using default.")
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
                filename=f"{base_filename}.{extension}",
                session=session
            )

    def get_urls(self, fileType = FileDownloadType.DEFAULT_FILE) -> list:
        urls = []

        def get_additional_urls():
            if not self.multiple_files:
                ASF_LOGGER.warning(f"You attempted to download multiple files from {self.properties['sceneName']}, this product only has one file to download.")
                return []

            additional_urls = []
            for url in self.properties['additionalUrls']:
                additional_urls.append(url)
            return additional_urls

        if fileType == FileDownloadType.DEFAULT_FILE:
            urls.append(self.properties['url'])
        elif fileType == FileDownloadType.ADDITIONAL_FILES:
            urls.extend(get_additional_urls())
        elif fileType == FileDownloadType.ALL_FILES:
            urls.append(self.properties['url'])
            urls.extend(get_additional_urls())
        else:
            raise ValueError("Invalid FileDownloadType provided, the valid types are 'DEFAULT_FILE', 'ADDITIONAL_FILES', and 'ALL_FILES'")
        return urls

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
        from .search.baseline_search import get_stack_opts

        return get_stack_opts(reference=self)

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

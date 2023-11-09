import os
import warnings
from shapely.geometry import shape, Point, Polygon, mapping
import json

from urllib import parse

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

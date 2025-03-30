from collections import UserList
from multiprocessing import Pool
import json
from typing import List
from asf_search import ASFSession, ASFSearchOptions
from asf_search.download.file_download_type import FileDownloadType
from asf_search.exceptions import ASFSearchError

from asf_search import ASF_LOGGER
from asf_search.export.csv import results_to_csv
from asf_search.export.jsonlite import results_to_jsonlite
from asf_search.export.jsonlite2 import results_to_jsonlite2
from asf_search.export.kml import results_to_kml
from asf_search.export.metalink import results_to_metalink


class ASFSearchResults(UserList):
    def __init__(self, *args, opts: ASFSearchOptions = None):
        super().__init__(*args)
        # Store it JUST so the user can access it (There might be zero products)
        # Each product will use their own reference to opts (but points to the same obj)
        self.searchOptions = opts
        self.searchComplete = False

    def geojson(self):
        return {
            'type': 'FeatureCollection',
            'features': [product.geojson() for product in self],
        }

    def csv(self):
        return results_to_csv(self)

    def kml(self):
        return results_to_kml(self)

    def metalink(self):
        return results_to_metalink(self)

    def jsonlite(self):
        return results_to_jsonlite(self)

    def jsonlite2(self):
        return results_to_jsonlite2(self)

    def find_urls(self, extension: str = None, pattern: str = r'.*', directAccess: bool = False) -> List[str]:
        """Returns a flat list of all https or s3 urls from all results matching an extension and/or regex pattern
        param extension: the file extension to search for. (Defaults to `None`)
            - Example: '.tiff'
        param pattern: A regex pattern to search each url for.(Defaults to `False`)
            - Example: `r'(QA_)+'` to find urls with 'QA_' at least once
        param directAccess: should search in s3 bucket urls (Defaults to `False`)
        """
        urls = []

        for product in self:
            urls.extend(product.find_urls(extension=extension, pattern=pattern, directAccess=directAccess))
        
        return sorted(list(set(urls)))
    
    def __str__(self):
        return json.dumps(self.geojson(), indent=2, sort_keys=True)

    def download(
        self,
        path: str,
        session: ASFSession = None,
        processes: int = 1,
        fileType=FileDownloadType.DEFAULT_FILE,
    ) -> None:
        """
        Iterates over each ASFProduct and downloads them to the specified path.

        Parameters
        ----------
        path:
            The directory into which the products should be downloaded.
        session:
            The session to use
            Defaults to the session used to fetch the results, or a new one if none was used.
        processes:
            Number of download processes to use. Defaults to 1 (i.e. sequential download)

        """
        ASF_LOGGER.info(f'Started downloading ASFSearchResults of size {len(self)}.')
        if processes == 1:
            for product in self:
                product.download(path=path, session=session, fileType=fileType)
        else:
            ASF_LOGGER.info(f'Using {processes} threads - starting up pool.')
            pool = Pool(processes=processes)
            args = [(product, path, session, fileType) for product in self]
            pool.map(_download_product, args)
            pool.close()
            pool.join()
        ASF_LOGGER.info(f'Finished downloading ASFSearchResults of size {len(self)}.')

    def raise_if_incomplete(self) -> None:
        if not self.searchComplete:
            msg = (
                'Results are incomplete due to a search error. '
                'See logging for more details. (ASFSearchResults.raise_if_incomplete called)'
            )

            ASF_LOGGER.error(msg)
            raise ASFSearchError(msg)

    def get_products_by_subclass_type(self) -> dict:
        """
        Organizes results into dictionary by ASFProduct subclass name
        : return: Dict of ASFSearchResults, organized by ASFProduct subclass names
        """
        subclasses = {}

        for product in self.data:
            product_type = product.get_classname()

            if subclasses.get(product_type) is None:
                subclasses[product_type] = ASFSearchResults([])

            subclasses[product_type].append(product)

        return subclasses


def _download_product(args) -> None:
    product, path, session, fileType = args
    product.download(path=path, session=session, fileType=fileType)

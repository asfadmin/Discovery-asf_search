from collections import UserList
from multiprocessing import Pool
import json
from asf_search import ASFSession, ASFSearchOptions
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
            'features': [product.geojson() for product in self]
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

    def __str__(self):
        return json.dumps(self.geojson(), indent=2, sort_keys=True)

    def download(
            self,
            path: str,
            session: ASFSession = None,
            processes: int = 1
    ) -> None:
        """
        Iterates over each ASFProduct and downloads them to the specified path.

        :param path: The directory into which the products should be downloaded.
        :param session: The session to use. Defaults to the session used to fetch the results, or a new one if none was used.
        :param processes: Number of download processes to use. Defaults to 1 (i.e. sequential download)

        :return: None
        """
        ASF_LOGGER.info(f"Started downloading ASFSearchResults of size {len(self)}.")
        if processes == 1:
            for product in self:
                product.download(path=path, session=session)
        else:
            ASF_LOGGER.info(f"Using {processes} threads - starting up pool.")
            pool = Pool(processes=processes)
            args = [(product, path, session) for product in self]
            pool.map(_download_product, args)
            pool.close()
            pool.join()
        ASF_LOGGER.info(f"Finished downloading ASFSearchResults of size {len(self)}.")
        
    def raise_if_incomplete(self) -> None:
        if not self.searchComplete:
            msg = "Results are incomplete due to a search error. See logging for more details. (ASFSearchResults.raise_if_incomplete called)"
            ASF_LOGGER.error(msg)
            raise ASFSearchError(msg)

def _download_product(args) -> None:
    product, path, session = args
    product.download(path=path, session=session)

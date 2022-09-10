from collections import UserList
from multiprocessing import Pool
import json
from asf_search import ASFSession, ASFSearchOptions


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

        if processes == 1:
            for product in self:
                product.download(path=path, session=session)
        else:
            pool = Pool(processes=processes)
            args = [(product, path, session) for product in self]
            pool.map(_download_product, args)
            pool.close()
            pool.join()

    def resume_search(self):
        from asf_search.search.search import search
        maxResults = self.searchOptions.maxResults - len(self)
        if self.searchComplete or maxResults <= 0:
            return

        remainder = search(opts=self.searchOptions, maxResults=maxResults)
        self.extend(remainder)
        # self.sort(key=lambda p: (p.properties['stopTime'], p.properties['fileID']), reverse=True)

        if len(self) == self.searchOptions.maxResults or 'CMR-Search-After' not in self.searchOptions.session.headers:
            self.searchComplete = True


def _download_product(args):
    product, path, session = args
    product.download(path=path, session=session)

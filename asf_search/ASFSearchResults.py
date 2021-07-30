from collections import UserList
from multiprocessing import Pool
import json
import requests


class ASFSearchResults(UserList):
    def geojson(self):
        return {
            'type': 'FeatureCollection',
            'features': [product.geojson() for product in self]
        }

    def __str__(self):
        return json.dumps(self.geojson(), indent=2, sort_keys=True)

    def download(self, path: str, session: requests.Session = None, processes=1) -> None:
        """
        Iterates over each ASFProduct and downloads them to the specified path.

        :param path: The directory into which the products should be downloaded.
        :param session: The session to use when downloading. This session should already be authenticated if that is required for the product in question. A blank session will be created if none is provided.
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


def _download_product(args):
    product, path, session = args
    product.download(path=path, session=session)

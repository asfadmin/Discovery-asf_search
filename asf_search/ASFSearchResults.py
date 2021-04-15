from collections import UserList
import json

from asf_search.ASFProduct import ASFProduct


class ASFSearchResults(UserList):
    def geojson(self):
        return {
            'type': 'FeatureCollection',
            'features': [product.geojson() for product in self]
        }

    def __str__(self):
        return json.dumps(self.geojson(), indent=2, sort_keys=True)

    def download(self, dir: str, token: str = None) -> None:
        """
        Iterates over each ASFProduct and downloads them to the specified directory.

        :param dir: The directory into which the products should be downloaded.
        :param token: EDL authentication token for authenticated downloads, see https://urs.earthdata.nasa.gov/user_tokens

        :return: None
        """

        for product in self:
            product.download(dir=dir, token=token)

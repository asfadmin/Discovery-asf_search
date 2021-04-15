from typing import Iterable
import numpy as np
import json
from collections import UserList

from asf_search.download import download_url


class ASFProduct:
    def __init__(self, args: dict):
        self.properties = args['properties']
        self.geometry = args['geometry']

    def __str__(self):
        return json.dumps(self.geojson(), indent=2, sort_keys=True)

    def geojson(self) -> dict:
        return {
            'type': 'Feature',
            'geometry': self.geometry,
            'properties': self.properties
        }

    def download(self, dir: str, filename: str = None, token: str = None) -> None:
        """
        Downloads this product to the specified path and optional filename.

        :param dir: The directory into which this product should be downloaded.
        :param filename: Optional filename to use instead of the original filename of this product.
        :param token: EDL authentication token for authenticated downloads, see https://urs.earthdata.nasa.gov/user_tokens

        :return: None
        """
        if filename is None:
            filename = self.properties['fileName']

        download_url(url=self.properties['url'], dir=dir, filename=filename, token=token)

    def stack(self) -> UserList:
        """
        Builds a baseline stack from this product.

        :return: ASFSearchResults(list) of the stack, with the addition of baseline values (temporal, perpendicular) attached to each ASFProduct.
        """
        from .search.baseline_search import stack_from_product

        return stack_from_product(self)

    def centroid(self) -> (Iterable[float]):
        """
        Finds the centroid of a product
        Shamelessly lifted from https://stackoverflow.com/a/23021198 and https://stackoverflow.com/a/57183264
        """
        arr = np.array(self.geometry['coordinates'][0])
        length, dim = arr.shape
        return [np.sum(arr[:, i]) / length for i in range(dim)]


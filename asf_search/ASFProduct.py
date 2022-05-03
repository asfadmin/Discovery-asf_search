from shapely.geometry import shape, Point, Polygon, mapping
import json
from collections import UserList
import requests

from asf_search.download import download_url
from asf_search import ASFSession


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

    def download(self, path: str, filename: str = None, session: ASFSession = None) -> None:
        """
        Downloads this product to the specified path and optional filename.

        :param path: The directory into which this product should be downloaded.
        :param filename: Optional filename to use instead of the original filename of this product.
        :param session: The session to use, in most cases should be authenticated beforehand

        :return: None
        """
        if filename is None:
            filename = self.properties['fileName']

        download_url(url=self.properties['url'], path=path, filename=filename, session=session)

    def stack(self) -> UserList:
        """
        Builds a baseline stack from this product.

        :return: ASFSearchResults(list) of the stack, with the addition of baseline values (temporal, perpendicular) attached to each ASFProduct.
        """
        from .search.baseline_search import stack_from_product

        return stack_from_product(self)

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

from shapely.geometry import shape, Point
import json
from collections import UserList

from asf_search.download import download_url
from asf_search import ASFSession
from asf_search import ASFSearchOptions


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

    def stack(
            self,
            opts: ASFSearchOptions = None
    ) -> UserList:
        """
        Builds a baseline stack from this product.

        :param opts: An ASFSearchOptions object describing the search parameters to be used. Search parameters specified outside this object will override in event of a conflict.

        :return: ASFSearchResults containing the stack, with the addition of baseline values (temporal, perpendicular) attached to each ASFProduct.
        """
        from .search.baseline_search import stack_from_product

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
        return shape(self.geometry).centroid

from shapely.geometry import shape, Point, Polygon, mapping
import json
from collections import UserList

from asf_search.download import download_url

from asf_search import ASFSession
from asf_search import ASFSearchOptions
from asf_search.CMR import translate_product

class ASFProduct:
    def __init__(self, args: dict, opts: ASFSearchOptions = None):
        self.meta = args['meta']
        self.umm = args['umm']

        translated = translate_product(args)

        self.properties = translated['properties']
        self.geometry = translated['geometry']
        self.baseline = translated['baseline']
        self.searchOptions = opts

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
        :param session: The session to use, defaults to the one used to find the results.

        :return: None
        """
        if filename is None:
            filename = self.properties['fileName']
        
        if session is None and self.searchOptions is not None:
            session = self.searchOptions.session

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
        # *this* opts, probably isn't the same as the one used to do the search.
        # Don't default to self.searchOptions here
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

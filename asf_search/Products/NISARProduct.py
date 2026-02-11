from datetime import datetime
import re
from asf_search.ASFSearchOptions import parse_int
from copy import copy
from dateutil.parser import parse as parse_datetime
from typing import Dict, Optional, Tuple, Union, Literal
from shapely import unary_union, multipolygons
from asf_search import ASFSearchOptions, ASFSession, ASFStackableProduct
from asf_search.CMR.translate import try_parse_frame_coverage, try_parse_bool, try_parse_int
from shapely.geometry import shape, MultiPolygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform
from asf_search.constants import PRODUCT_TYPE

STATIC_PATTERN_STR = (
    r'NISAR_L2_STATIC_.*_(?P<posting>\d{3}_{3})_(?:\d{8}T\d{6})_(?:R\d{5})_\D_(?P<counter>\d{3})'
)
STATIC_PATTERN = re.compile(STATIC_PATTERN_STR)


class NISARProduct(ASFStackableProduct):
    """
    Used for NISAR dataset products

    ASF Dataset Documentation Page: https://asf.alaska.edu/nisar/
    """

    _base_properties = {
        **ASFStackableProduct._base_properties,
        'frameNumber': {
            'path': ['AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0],
            'cast': try_parse_int,
        },  # Sentinel, ALOS and NISAR product alt for frameNumber (ESA_FRAME)
        'pathNumber': {  # AKA trackNumber, AKA relativeOrbit
            'path': ['AdditionalAttributes', ('Name', 'TRACK_NUMBER'), 'Values', 0],
            'cast': try_parse_int,
        },
        'pgeVersion': {'path': ['PGEVersionClass', 'PGEVersion']},
        'crid': {'path': ['DataGranule', 'Identifiers', ('IdentifierType', 'CRID'), 'Identifier']},
        'mainBandPolarization': {
            'path': ['AdditionalAttributes', ('Name', 'FREQUENCY_A_POLARIZATION'), 'Values']
        },
        'sideBandPolarization': {
            'path': ['AdditionalAttributes', ('Name', 'FREQUENCY_B_POLARIZATION'), 'Values']
        },
        'frameCoverage': {
            'path': ['AdditionalAttributes', ('Name', 'FULL_FRAME'), 'Values', 0],
            'cast': try_parse_frame_coverage,
        },
        'jointObservation': {
            'path': ['AdditionalAttributes', ('Name', 'JOINT_OBSERVATION'), 'Values', 0],
            'cast': try_parse_bool,
        },
        'rangeBandwidth': {
            'path': ['AdditionalAttributes', ('Name', 'RANGE_BANDWIDTH_CONCAT'), 'Values']
        },
        'productionConfiguration': {
            'path': ['AdditionalAttributes', ('Name', 'PRODUCTION_PIPELINE'), 'Values', 0]
        },
        'processingLevel': {
            'path': ['AdditionalAttributes', ('Name', 'PRODUCT_TYPE'), 'Values', 0]
        },
        'bytes': {'path': ['DataGranule', 'ArchiveAndDistributionInformation']},
        'collectionName': {'path': ['CollectionReference', 'ShortName']},
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        if self.properties.get('processingLevel') is None:
            self.properties.pop('processingLevel', None)

        self.properties['additionalUrls'] = self._get_additional_urls()
        self.properties['browse'] = [
            url
            for url in self._get_urls()
            if url.endswith('.png') or url.endswith('.jpg') or url.endswith('.jpeg')
        ]
        self.properties['s3Urls'] = self._get_s3_uris()

        if self.properties.get('groupID') is None:
            self.properties['groupID'] = self.properties['sceneName']
        self.properties['bytes'] = {
            entry['Name']: {'bytes': entry['SizeInBytes'], 'format': entry['Format']}
            for entry in self.properties['bytes']
        }
        self.properties['conceptID'] = self.umm_get(self.meta, 'collection-concept-id')

        if self.properties.get('collectionName') == 'NISAR_L2_STATIC':
            posting = STATIC_PATTERN.match(self.properties['sceneName'])
            if posting is not None:
                static_props = posting.groupdict()
    
                postings = static_props['posting'].split('_')
                self.properties['posting'] = (postings[0], postings[1])
                self.properties['crid_counter'] = static_props['crid_counter']
            # posting = ''

    @staticmethod
    def get_default_baseline_product_type() -> Union[str, None]:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return None

    def is_valid_reference(self):
        return False

    def get_stack_opts(self, opts: ASFSearchOptions = None) -> ASFSearchOptions:
        """
        Build search options that can be used to find an insar stack for this product

        :return: ASFSearchOptions describing appropriate options
        for building a stack from this product
        """
        return None

    def get_sort_keys(self) -> Tuple[str, str]:
        keys = super().get_sort_keys()

        if keys[0] == '':
            return (self._read_property('processingDate', ''), keys[1])

        return keys

    def get_static_layer(
        self,
        frequency: Literal['A', 'B'] | None = None,
        posting: tuple[str] | None = None,
        opts: ASFSearchOptions | None = None,
    ) -> Optional['NISARProduct']:
        """Returns the equivalent static layer for the given NISAR Level 2 static product

        Parameters
        ----------
        frequency: Literal['A', 'B'] (optional):
            Overrides which post mapping to use (defaults to 'A' if range bandwidth is non-zero, otherwise 'B')
        posting: tuple[str] (optional):
            Provide a preferred posting desired for a static layer manually (in the form of triple digit integer strings `('000', '000)`)
        opts: ASFSearchOptions (optional):
            additional search opts to use when querying CMR for static layers. (NOTE: `relativeOrbit`, `frame`, `end`, `shortName` will all be overriden in the final search)

        Yields
        -------
        Desired static layer NISARProduct for the current L2 NISARProduct
        """

        if self.properties.get('processingLevel') not in [
            PRODUCT_TYPE.GSLC,
            PRODUCT_TYPE.GCOV,
            PRODUCT_TYPE.GUNW,
            PRODUCT_TYPE.GOFF,
        ]:
            return None

        static_opts = ASFSearchOptions() if opts is None else copy(opts)

        static_opts.relativeOrbit = self.properties['pathNumber']
        static_opts.frame = self.properties['frameNumber']
        static_opts.end = self.properties['startTime']
        # if static_opts.shortName is None:
        static_opts.shortName = 'NISAR_L2_STATIC'

        from asf_search import search

        response = search(opts=static_opts)

        cutoff_datetime = datetime.fromisoformat(self.properties['startTime'])
        response = [
            product
            for product in sorted(
                filter(
                    lambda x: (
                        cutoff_datetime
                        > datetime.fromisoformat(x.properties.get('validityStartDate'))
                    ),
                    response,
                ),
                key=lambda x: parse_datetime(x.properties.get('validityStartDate')),
                reverse=True,
            )
        ]

        postings = [posting]
        if posting is None:
            bandwidths = self.properties['rangeBandwidth'].split('+')
            if frequency is None:
                if parse_int(bandwidths[0]) == 0:
                    frequency = 'A'
                else:
                    frequency = 'B'

            bandwidth_frequency = bandwidths[0] if frequency == 'A' else bandwidths[1]
            postings = self.get_postings_for_frequency(
                self.properties['processingLevel'], bandwidth_frequency
            )

        latest_valid = None
        for p in postings:
            for product in response:
                if product.properties['posting'] == p:
                    if latest_valid is None:
                        latest_valid = product
                    else:
                        if parse_datetime(product.properties.get('validityStartDate')) == parse_datetime(latest_valid.properties.get('validityStartDate')):
                            if int(product.properties['crid_counter']) > int(latest_valid.properties['crid_counter']):
                                latest_valid = product
                        else:
                            # results pre-sorted by latest validity start time, if there's no similar product with a higher crid counter
                            # we've found the latest
                            break
            
            if latest_valid is not None:
                return latest_valid

    def _get_geometry(self, item: Dict) -> dict:
        """Overload for dateline multipolygon parsing.
        # TODO consider implications of moving this to base ASFProduct class in future
        """
        try:
            polygons = item['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry'][
                'GPolygons'
            ]
            # dateline spanning scenes are stored as multiple polygons in CMR,
            # we need to unwrap and merge them
            if len(polygons) > 1:
                polygon_shapes = []
                for polygon in polygons:
                    coordinates = [
                        [c['Longitude'], c['Latitude']] for c in polygon['Boundary']['Points']
                    ]
                    geometry = self._get_unwrapped(
                        {'coordinates': [coordinates], 'type': 'Polygon'}
                    )

                    polygon_shapes.append(geometry)

                geom = unary_union(multipolygons(polygon_shapes))

                # sometimes the dateline spanning polygons don't overlap properly
                if isinstance(geom, MultiPolygon):
                    geom = geom.convex_hull

                return {'coordinates': [geom.exterior.coords], 'type': 'Polygon'}
            else:
                coordinates = polygons[0]['Boundary']['Points']
                coordinates = [[c['Longitude'], c['Latitude']] for c in coordinates]
                geometry = {'coordinates': [coordinates], 'type': 'Polygon'}
        except KeyError:
            geometry = {'coordinates': None, 'type': 'Polygon'}

        return geometry

    def _get_unwrapped(self, geometry: dict) -> BaseGeometry:
        def unwrap_shape(x, y, z=None):
            x = x if x > 0 else x + 360
            return tuple([x, y])

        wrapped = shape(geometry)
        if wrapped.bounds[0] < 0 or wrapped.bounds[2] < 0:
            unwrapped = transform(unwrap_shape, wrapped)
        else:
            unwrapped = wrapped

        return unwrapped

    @staticmethod
    def get_postings_for_frequency(
        processingLevel: str, bandwidth_frequency: int
    ) -> list[tuple[str, str]]:
        return NISARProduct._FREQ_POSTING_MAP[processingLevel][bandwidth_frequency]

    _FREQ_POSTING_MAP = {
        'GCOV': {
            5: [('080', '080'), ('020', '020'), ('010', '010')],
            20: [('020', '020'), ('010', '010'), ('080', '080')],
            77: [('020', '020'), ('010', '010'), ('080', '080')],
            40: [('010', '010'), ('020', '020'), ('080', '080')],
        },
        'GSLC': {
            5: [
                ('005', '040'),
                ('005', '010'),
                ('005', '005'),
                ('005', '2.5'),
                ('010', '010'),
                ('020', '020'),
                ('080', '080'),
            ],
            20: [
                ('005', '010'),
                ('005', '005'),
                ('005', '2.5'),
                ('005', '040'),
                ('010', '010'),
                ('020', '020'),
                ('080', '080'),
            ],
            40: [
                ('005', '005'),
                ('005', '2.5'),
                ('005', '010'),
                ('005', '040'),
                ('010', '010'),
                ('020', '020'),
                ('080', '080'),
            ],
            77: [
                ('005', '2.5'),
                ('005', '005'),
                ('005', '010'),
                ('005', '040'),
                ('010', '010'),
                ('020', '020'),
                ('080', '080'),
            ],
        },
        # in vertex, GUNW should return both 080 and 020 version
        'GUNW': {
            20: [('080', '080'), ('020', '020'), ('010', '010')],
            40: [('080', '080'), ('020', '020'), ('010', '010')],
            77: [('080', '080'), ('020', '020'), ('010', '010')],
        },
        'GOFF': {
            20: [('080', '080'), ('020', '020'), ('010', '010')],
            40: [('080', '080'), ('020', '020'), ('010', '010')],
            77: [('080', '080'), ('020', '020'), ('010', '010')],
        },
    }

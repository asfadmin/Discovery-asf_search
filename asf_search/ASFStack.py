from copy import deepcopy
from datetime import datetime
from typing import List

import numpy as np
from shapely import geometry, intersection_all, unary_union

import asf_search

DATE_FMT = '%Y-%m-%dT%H:%M:%SZ'
SIMPLIFY_TOL = 0.001


def get_unique_properties(products: List[asf_search.ASFProduct], key: str):
    return list(set([product.properties[key] for product in products]))


class ASFProductGroup:
    """A group of ASFProducts that forms a valid InSAR group. This means all products:
    - Are from the same pass of a platform
    - Have the same beam mode
    - Contain at least one common polarization
    - Are contiguous in space

    Parameters
    ----------
    `products`:
        A list of ASFProducts from the same pass of a platform.
    """

    def __init__(self, products: List[asf_search.ASFProduct]):
        self.validate_group(products)
        orbits = list(set([product.properties['orbit'] for product in products]))
        self.orbit = orbits[0]
        self.relative_orbit = products[0].properties['pathNumber']
        footprints = [geometry.shape(product.geometry) for product in products]
        self.footprint = unary_union(footprints).simplify(SIMPLIFY_TOL)
        dates = [
            datetime.strptime(product.properties['stopTime'], DATE_FMT) for product in products
        ]
        self.date = min(dates)
        self.products = sorted(
            products, key=lambda x: datetime.strptime(x.properties['stopTime'], DATE_FMT)
        )

    @staticmethod
    def validate_group(products: List[asf_search.ASFProduct]):
        """Check if a list of products are from the same pass of a platform."""

        if len(products) == 0:
            raise asf_search.ASFGroupError('At least one product is required')

        platforms = get_unique_properties(products, 'platform')
        if len(platforms) != 1:
            raise asf_search.ASFGroupError('All products must be from the same platform')

        processing_level = get_unique_properties(products, 'processingLevel')
        # In the future, allow products other than S1 Bursts
        if not processing_level[0] == 'BURST' and platforms[0].startswith('SENTINEL'):
            raise NotImplementedError('Only Sentinel-1 Burst products are currently supported')

        beam_modes = get_unique_properties(products, 'beamModeType')
        if len(beam_modes) != 1:
            raise asf_search.ASFGroupError('All products must have the same beam mode')

        polarizations = get_unique_properties(products, 'polarization')
        if len(polarizations) != 1:
            raise asf_search.ASFGroupError('All products must have the same polarization')

        dates = [
            datetime.strptime(product.properties['stopTime'], DATE_FMT) for product in products
        ]
        orbits = get_unique_properties(products, 'orbit')
        pass_msg = 'All products must be from the same pass of a platform'
        if len(orbits) > 2:
            raise asf_search.ASFGroupError(pass_msg)
        if len(orbits) == 2:
            if max(orbits) - min(orbits) != 1:
                raise asf_search.ASFGroupError(pass_msg)
            if (max(dates) - min(dates)).minutes > 5:
                raise asf_search.ASFGroupError(pass_msg)

        footprints = [geometry.shape(product.geometry) for product in products]
        union = unary_union(footprints)
        assert not union.is_empty, 'Products must overlap in space'

    def get_granule_ids(self) -> List[str]:
        """Return the granule IDs of the products in the group."""
        return [product.properties['fileID'] for product in self.products]

    def __len__(self) -> int:
        return len(self.products)

    def __repr__(self):
        return f'ASFProductGroup: orbit={self.orbit}, date={self.date}, n={self.__len__()}'


class ASFStack:
    """A sef of ASFProduct groups that form a valid InSAR stack. This means all groups:
    - Are from the same relative orbit
    - Have the same beam mode
    - Contain at least one common polarization
    - Overlap in space

    Groups are sorted from earliest to latest date.

    Parameters
    ----------
    `products`:
        A list of ASFProducts from the same relative orbit.
    """

    def __init__(self, products: List[asf_search.ASFProduct]):
        self.groups = self.group_products(products)
        footprints = [group.footprint for group in self.groups]
        self.union_footprint = unary_union(footprints).simplify(SIMPLIFY_TOL)
        assert not self.union_footprint.is_empty, 'Groups must overlap in space'
        self.intersect_footprint = intersection_all(footprints).simplify(SIMPLIFY_TOL)
        self.start_date = min([group.date for group in self.groups])
        self.end_date = max([group.date for group in self.groups])
        self.dates = [group.date for group in self.groups]
        self.relative_orbit = self.groups[0].relative_orbit

    @staticmethod
    def filter_by_orbit(products: List[asf_search.ASFProduct], orbit: int):
        return [product for product in products if product.properties['orbit'] == orbit]

    def group_products(self, products: List[asf_search.ASFProduct]):
        """Group a set of products into a valid InSAR group."""
        rel_orbits = list(set([product.properties['pathNumber'] for product in products]))
        assert len(rel_orbits) == 1, 'All products must be from the same relative orbit'
        abs_orbits = sorted(list(set([product.properties['orbit'] for product in products])))
        product_groups = [self.filter_by_orbit(products, abs_orbits[0])]
        for i, orbit in enumerate(abs_orbits[1:]):
            if orbit - abs_orbits[i - 1] == 1:
                product_groups[-1] += self.filter_by_orbit(products, orbit)
            else:
                product_groups.append(self.filter_by_orbit(products, orbit))
        product_groups = [ASFProductGroup(group) for group in product_groups]
        return sorted(product_groups, key=lambda x: x.date)

    def get_overlap_pct(self, geometry):
        """Return the percentage of the stack that overlaps with the given geometry."""
        overlap_pct = self.intersect_footprint.intersection(geometry).area / geometry.area
        return int(overlap_pct * 100)

    def get_granule_ids(self) -> List[List[str]]:
        """Return the granule IDs of the products in the stack."""
        return [group.get_granule_ids() for group in self.groups]

    def construct_network(self, max_temporal_baseline: int = 30, max_perpendicular_baseline: float = 300):
        """Construct a network of ASFProductPairs using the baseline constraints.

        Parameters
        ----------
        `max_temporal_baseline`:
            The maximum number of days between a reference and secondary group (always positive).
        `max_perpendicular_baseline`:
            The maximum distance between the platform position during the collection
            of the reference and secondary groups (always positive).
        """
        return ASFPairNetwork(self, max_temporal_baseline, max_perpendicular_baseline)

    def __len__(self) -> int:
        return len(self.groups)

    def __repr__(self):
        return f'ASFStack: relative_orbit={self.relative_orbit}, start_date={self.start_date}, end_date={self.end_date}, n={self.__len__()}'


class ASFProductPair:
    """A pair of ASFProductGroups from that form a valid InSAR pair. This means the groups:
    - Are from the same relative orbit
    - Have the same beam mode
    - Contain at least one common polarization
    - Overlap in space

    Reference is the earlier group and secondary is the later group regardless of the order of the input groups.

    Parameters
    ----------
    `group1`:
        An ASFProductGroup
    `group2`:
        An ASFProductGroup
    """

    def __init__(self, group1, group2):
        sorted_pair = sorted([group1, group2], key=lambda x: x.date)
        self.relative_orbit = sorted_pair[0].relative_orbit
        self.reference = sorted_pair[0]
        self.reference_date = self.reference.date
        self.secondary = sorted_pair[1]
        self.secondary_date = self.secondary.date
        self.footprint = self.reference.footprint.intersection(self.secondary.footprint).simplify(
            SIMPLIFY_TOL
        )
        reference_name = self.reference.products[0].properties['sceneName']
        products = [self.reference.products[0], self.secondary.products[0]]
        products = asf_search.calculate_perpendicular_baselines(reference_name, products)
        products = asf_search.calculate_temporal_baselines(products[0], products)
        self.perpendicular_baseline = products[1].properties['perpendicularBaseline']
        self.temporal_baseline = products[1].properties['temporalBaseline']

    def get_granule_ids(self) -> List[List[str]]:
        """Return the granule IDs of the products in the stack."""
        return [group.get_granule_ids() for group in (self.reference, self.secondary)]

    def __repr__(self):
        return f'ASFProductPair: relative_oribt={self.relative_orbit}, ref_date={self.reference_date}, sec_date={self.secondary_date}, perp_baseline={self.perpendicular_baseline}'


class ASFPairNetwork:
    """A network of ASFProductPairs that form a valid InSAR network. This means all pairs:
    - Are from the same relative orbit
    - Have the same beam mode
    - Contain at least one common polarization
    - Overlap in space

    ASFPairs are formed using earlier products as the reference and later products as the secondary.

    Parameters
    ----------
    `stack`:
        An ASFStack
    `max_temporal_baseline`:
        The maximum number of days between a reference and secondary group (always positive).
    `max_perpendicular_baseline`:
        The maximum distance betwee the platform postion during the collection
        of the reference and secondary groups (always positive).
    """

    def __init__(
        self,
        stack: ASFStack,
        max_temporal_baseline: int = 30,
        max_perpendicular_baseline: float = 300,
    ):
        assert max_temporal_baseline >= 0, 'Max temporal baseline must be positive'
        assert max_perpendicular_baseline >= 0, 'Max perpendicular baseline must be positive'
        self.stack = stack
        self.max_temporal_baseline = max_temporal_baseline
        self.max_perpendicular_baseline = max_perpendicular_baseline
        self.pairs = self.construct_network()
        self.relative_orbit = self.stack.groups[0].relative_orbit
        self.start_date = self.pairs[0].reference_date
        self.end_date = self.pairs[-1].secondary_date
        footprints = [pair.footprint for pair in self.pairs]
        self.union_footprint = unary_union(footprints).simplify(SIMPLIFY_TOL)
        self.intersect_footprint = intersection_all(footprints).simplify(SIMPLIFY_TOL)

    def construct_network(self):
        """Construct a network of ASFProductPairs using the baseline constraints."""
        groups = self.stack.groups
        pairs = []
        for i, ref in enumerate(groups):
            for sec in groups[i + 1 :]:
                pair = ASFProductPair(ref, sec)
                if pair.temporal_baseline > self.max_temporal_baseline:
                    break
                if np.abs(pair.perpendicular_baseline) < self.max_perpendicular_baseline:
                    pairs.append(pair)
        pairs = sorted(pairs, key=lambda x: (x.reference_date, x.secondary_date))
        return pairs

    def plot(self):
        """Construct an SBAS plot of the ASFPairNetwork."""
        try:
            import matplotlib.dates as mdates
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError('Matplotlib must be installed to plot ASFPairNetworks')
        products = [deepcopy(group.products[0]) for group in self.stack.groups]
        ref_loc = len(products) // 2
        reference = products[ref_loc]

        reference_name = reference.properties['sceneName']
        reference_date = datetime.strptime(reference.properties['stopTime'], DATE_FMT)
        products = asf_search.calculate_perpendicular_baselines(reference_name, products)
        perp_baselines = [product.properties['perpendicularBaseline'] for product in products]
        dates = [
            datetime.strptime(product.properties['stopTime'], DATE_FMT) for product in products
        ]
        points = {date: (date, perp) for date, perp in zip(dates, perp_baselines)}
        ref_point = points[reference_date]

        fig, ax = plt.subplots()
        for i, pair in enumerate(self.pairs):
            kwgs = {'label': 'Pairs'} if i == 0 else {}
            line = zip(*[points[pair.reference_date], points[pair.secondary_date]])
            ax.plot(*line, color='blue', zorder=0, **kwgs)
        ax.scatter(*zip(*points.values()), color='gray', zorder=1, label='Products')
        ax.scatter(*ref_point, color='red', zorder=2, label='Reference')
        ax.set_xlabel('Date')
        ax.set_ylabel('Perpendicular Baseline (m)')
        ax.legend()
        locator = mdates.AutoDateLocator()
        formatter = mdates.AutoDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    def get_granule_ids(self) -> List[List[List[str]]]:
        """Return the granule IDs of the products in the stack."""
        return [pair.get_granule_ids() for pair in self.pairs]

    def __len__(self) -> int:
        return len(self.pairs)

    def __repr__(self):
        return f'ASFPairNetwork: relative_orbit={self.relative_orbit}, temporal_baseline={self.max_temporal_baseline}, perpendicular_baseline={self.max_perpendicular_baseline}, n={self.__len__()}'

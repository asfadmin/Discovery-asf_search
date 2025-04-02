from copy import deepcopy
from datetime import datetime
from typing import List

import numpy as np
from shapely import geometry, intersection_all, unary_union

import asf_search

DATE_FMT = '%Y-%m-%dT%H:%M:%SZ'


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
        orbits = list(set([product.properties['orbit'] for product in products]))
        assert len(orbits) == 1, 'All products must be from the same absolute orbit'
        self.orbit = orbits[0]
        self.relative_orbit = products[0].properties['pathNumber']
        footprints = [geometry.shape(product.geometry) for product in products]
        self.footprint = unary_union(footprints).simplify(0.001)
        dates = [
            datetime.strptime(product.properties['stopTime'], DATE_FMT) for product in products
        ]
        self.date = min(dates)
        self.length = len(products)
        self.products = sorted(
            products, key=lambda x: datetime.strptime(x.properties['stopTime'], DATE_FMT)
        )
        # TODO: add group validation

    def __repr__(self):
        return f'ASFProductGroup: orbit={self.orbit}, date={self.date}, n={self.length}'


class ASFStack:
    """A sef of ASFProduct groups that form a valid InSAR stack. This means all groups:
    - Are from the same relative orbit
    - Have the same beam mode
    - Contain at least one common polarization
    - Overlap in space

    Groups are sorted from earliest to latest date.

    Parameters
    ----------
    `search_result`:
        A list of search results from asf_search.search_asf that meet the above criteria.
    """

    def __init__(self, search_result: List[asf_search.ASFProduct]):
        self.groups = self.group_search_results(search_result)
        footprints = [group.footprint for group in self.groups]
        self.union_footprint = unary_union(footprints).simplify(0.001)
        self.intersect_footprint = intersection_all(footprints).simplify(0.001)
        self.start_date = min([group.date for group in self.groups])
        self.end_date = max([group.date for group in self.groups])
        self.dates = [group.date for group in self.groups]
        self.relative_orbit = self.groups[0].relative_orbit
        self.length = len(self.groups)

    def group_search_results(self, search_result: List[asf_search.ASFProduct]):
        """Group a set of search results into a valid InSAR group."""
        abs_orbits = list(set([result.properties['orbit'] for result in search_result]))
        # FIXME: Does not account for ascending pass orbit increment
        product_groups = [
            [r for r in search_result if r.properties['orbit'] == orbit] for orbit in abs_orbits
        ]
        product_groups = [ASFProductGroup(group) for group in product_groups]
        return sorted(product_groups, key=lambda x: x.date)

    def get_overlap_pct(self, geometry):
        """Return the percentage of the stack that overlaps with the given geometry."""
        overlap_pct = self.intersect_footprint.intersection(geometry).area / geometry.area
        return int(overlap_pct * 100)

    def __repr__(self):
        return f'ASFStack: relative_orbit={self.relative_orbit}, start_date={self.start_date}, end_date={self.end_date}, n={self.length}'


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
            0.001
        )
        reference_name = self.reference.products[0].properties['sceneName']
        products = [self.reference.products[0], self.secondary.products[0]]
        products = asf_search.calculate_perpendicular_baselines(reference_name, products)
        products = asf_search.calculate_temporal_baselines(products[0], products)
        self.perpendicular_baseline = products[1].properties['perpendicularBaseline']
        self.temporal_baseline = products[1].properties['temporalBaseline']

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
        self.union_footprint = unary_union(footprints).simplify(0.001)
        self.intersect_footprint = intersection_all(footprints).simplify(0.001)
        self.length = len(self.pairs)

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
        products = [deepcopy(group.products[0]) for group in self.stack]
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

    def __repr__(self):
        return f'ASFPairNetwork: relative_orbit={self.relative_orbit}, temporal_baseline={self.max_temporal_baseline}, perpendicular_baseline={self.max_perpendicular_baseline}, n={len(self.pairs)}'

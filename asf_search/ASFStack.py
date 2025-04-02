from copy import deepcopy
from datetime import datetime

import numpy as np
from shapely import geometry, intersection_all, unary_union

import asf_search


class ASFProductGroup:
    """A set of ASFProducts from one pass of a platform."""

    def __init__(self, products):
        orbits = list(set([product.properties['orbit'] for product in products]))
        assert len(orbits) == 1, 'All products must be from the same absolute orbit'
        self.orbit = orbits[0]
        self.relative_orbit = products[0].properties['pathNumber']
        footprints = [geometry.shape(product.geometry) for product in products]
        self.footprint = unary_union(footprints).simplify(0.001)
        fmt = '%Y-%m-%dT%H:%M:%SZ'
        dates = [datetime.strptime(product.properties['stopTime'], fmt) for product in products]
        self.date = min(dates)
        self.length = len(products)
        self.products = sorted(
            products, key=lambda x: datetime.strptime(x.properties['stopTime'], fmt)
        )

    def __repr__(self):
        return f'ASFProductGroup(orbit={self.orbit}, date={self.date}, n={self.length})'


class ASFStack:
    """A nested group of products that form valid InSAR groupings."""

    def __init__(self, search_result):
        # check same product type, mission, and mode
        self.stack = self.group_search_results(search_result)
        footprints = [group.footprint for group in self.stack]
        self.union_footprint = unary_union(footprints).simplify(0.001)
        self.intersect_footprint = intersection_all(footprints).simplify(0.001)
        self.start_date = min([group.date for group in self.stack])
        self.end_date = max([group.date for group in self.stack])
        self.dates = [group.date for group in self.stack]
        self.relative_orbit = self.stack[0].relative_orbit
        self.length = len(self.stack)

    def group_search_results(self, search_result):
        """Group a set of search results into an interferometrically valid group.

        Returns:
            A date-sorted list of ASFProductGroups
        """
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
        return f'ASFStack(relative_orbit={self.relative_orbit}, start_date={self.start_date}, end_date={self.end_date}, n={self.length})'


class ASFProductPair:
    """A pair of ASFProductGroups from the same relative orbit."""

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
        return f'ASFProductPair(relative_oribt={self.relative_orbit}, ref_date={self.reference_date}, sec_date={self.secondary_date}, perp_baseline={self.perpendicular_baseline})'


class ASFPairNetwork:
    """A network of ASFProductPairs from the same relative orbit."""

    def __init__(self, stack, max_temporal_baseline=30, max_perpendicular_baseline=300):
        self.stack = stack
        self.max_temporal_baseline = max_temporal_baseline
        self.max_perpendicular_baseline = max_perpendicular_baseline
        self.pairs = self.construct_network()
        self.relative_orbit = self.stack[0].relative_orbit
        self.start_date = self.pairs[0].reference_date
        self.end_date = self.pairs[-1].secondary_date
        footprints = [pair.footprint for pair in self.pairs]
        self.union_footprint = unary_union(footprints).simplify(0.001)
        self.intersect_footprint = intersection_all(footprints).simplify(0.001)
        self.length = len(self.pairs)

    def construct_network(self):
        assert self.max_temporal_baseline >= 0, 'Max temporal baseline must be positive'
        assert self.max_perpendicular_baseline >= 0, 'Max perpendicular baseline must be positive'
        pairs = []
        for i, ref in enumerate(self.stack):
            for sec in self.stack[i + 1 :]:
                pair = ASFProductPair(ref, sec)
                if pair.temporal_baseline > self.max_temporal_baseline:
                    break
                if np.abs(pair.perpendicular_baseline) < self.max_perpendicular_baseline:
                    pairs.append(pair)
        pairs = sorted(pairs, key=lambda x: (x.reference_date, x.secondary_date))
        return pairs

    def get_pair_line_for_plot(self, pair, points):
        ref_loc = points.index(pair.reference_date)
        sec_loc = points.index(pair.secondary_date)
        return [(ref_loc, pair.perpendicular_baseline), (sec_loc, pair.perpendicular_baseline)]

    def plot(self):
        try:
            import matplotlib.dates as mdates
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError('Matplotlib must be installed to plot ASFPairNetworks')
        fmt = '%Y-%m-%dT%H:%M:%SZ'
        products = [deepcopy(group.products[0]) for group in self.stack]
        ref_loc = len(products) // 2
        reference = products[ref_loc]

        reference_name = reference.properties['sceneName']
        reference_date = datetime.strptime(reference.properties['stopTime'], fmt)
        products = asf_search.calculate_perpendicular_baselines(reference_name, products)
        perp_baselines = [product.properties['perpendicularBaseline'] for product in products]
        dates = [datetime.strptime(product.properties['stopTime'], fmt) for product in products]
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
        return f'ASFPairNetwork(relative_orbit={self.relative_orbit}, temporal_baseline={self.max_temporal_baseline}, perpendicular_baseline={self.max_perpendicular_baseline}, n={len(self.pairs)})'

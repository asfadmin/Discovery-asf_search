import math

from asf_search import ASFProduct
from asf_search.baseline import calc
from asf_search.baseline import calculate_perpendicular_baselines
import pytz

try:
    from ciso8601 import parse_datetime
except ImportError:
    from dateutil.parser import parse as parse_datetime


# This function should be in baseline.calc and be called by calculate_perpendicular_baselines
# calculate_perpendicular_baselines should handle refernce scenes without relative_sv_pre_time and
# relative_sv_post_time already set. This function could be used for the ref scene and all products in stack
def get_rel_sv_times(product: ASFProduct):
    baselineProperties = product.baseline
    positionProperties = baselineProperties["stateVectors"]["positions"]
    product.baseline["granulePosition"] = calc.get_granule_position(
        product.properties["centerLat"], product.properties["centerLon"]
    )

    asc_node_time = parse_datetime(
        baselineProperties["ascendingNodeTime"]
    ).timestamp()

    start = parse_datetime(product.properties["startTime"]).timestamp()
    end = parse_datetime(product.properties["stopTime"]).timestamp()
    center = start + ((end - start) / 2)
    baselineProperties["relative_start_time"] = start - asc_node_time
    baselineProperties["relative_center_time"] = center - asc_node_time
    baselineProperties["relative_end_time"] = end - asc_node_time

    t_pre = parse_datetime(positionProperties["prePositionTime"]).timestamp()
    t_post = parse_datetime(positionProperties["postPositionTime"]).timestamp()
    product.baseline["relative_sv_pre_time"] = t_pre - asc_node_time
    product.baseline["relative_sv_post_time"] = t_post - asc_node_time


class Pair:
    def __init__(self, reference: ASFProduct, secondary: ASFProduct):
        self.reference = reference
        self.secondary = secondary

        get_rel_sv_times(reference)
        self.perpendicular = calculate_perpendicular_baselines(reference, [secondary])[0].properties['perpendicularBaseline']

        reference_time = parse_datetime(reference.properties["startTime"])
        if reference_time.tzinfo is None:
            reference_time = pytz.utc.localize(reference_time)
        secondary_time = parse_datetime(secondary.properties["startTime"])
        if secondary_time.tzinfo is None:
            secondary_time = pytz.utc.localize(secondary_time)
        self.temporal = secondary_time.date() - reference_time.date()

    def estimate_mean_coherence(self) -> float:
        '''
        Estimates mean coherence for a pair using the 11367x4367 overview of the 2019-2020 
        VV COH data from the Global Seasonal Sentinel-1 Interferometric Coherence and Backscatter Dataset:
        https://asf.alaska.edu/datasets/daac/global-seasonal-sentinel-1-interferometric-coherence-and-backscatter-dataset/

        To support effecient in-place subsetting and access, the VV COH data has been saved to a public Zarr Store in AWS S3:
        s3://asf-search-coh/global_coh_100ppd_11367x4367

        Returns:
        '''
        # TODO: make xarray an optional dependency
        import xarray as xr

        month = parse_datetime(self.reference.properties["startTime"]).month
        if month in [12, 1, 2]:
            season = 'winter'
        elif month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        elif month in [9, 10, 11]:
            season = 'fall'

        temporal = math.ceil(self.temporal.days / 6) * 6
        if temporal > 48:
            raise Exception(
                (f"""Coherence dataset includes temporal baselines up to 48 days.
            Temporal baseline: {self.temporal.days} days"""))

        uri = f"s3://asf-search-coh/global_coh_100ppd_11367x4367/Global_{season}_vv_COH{temporal}_100ppd.zarr"
        coords = self.reference.geometry['coordinates'][0]
        lons, lats = zip(*coords)
        minx, miny, maxx, maxy = min(lons), min(lats), max(lons), max(lats)

        ds = xr.open_zarr(
            uri,
            consolidated=True
            )
        ds = ds.rio.write_crs("EPSG:4326", inplace=False)
        subset = ds.rio.clip_box(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
        return subset.coherence.mean().compute().item()

# TODO: add hyp3_safe()

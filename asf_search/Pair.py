import math

from asf_search import ASFProduct
from asf_search.baseline import calculate_perpendicular_baselines
import pytz

try:
    from ciso8601 import parse_datetime
except ImportError:
    from dateutil.parser import parse as parse_datetime


class Pair:
    def __init__(self, reference: ASFProduct, secondary: ASFProduct):
        self.reference = reference
        self.secondary = secondary

        self.perpendicular = calculate_perpendicular_baselines(
            reference.properties['sceneName'], 
            [secondary, reference])[0].properties['perpendicularBaseline']

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

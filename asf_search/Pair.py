
import importlib.util
import math
import warnings

from .ASFProduct import ASFProduct
from .baseline import calculate_perpendicular_baselines
from .exceptions import CoherenceEstimationError
from .warnings import OptionalDependencyWarning
import pytz

try:
    from ciso8601 import parse_datetime
except ImportError:
    from dateutil.parser import parse as parse_datetime


class Pair:
    """
    A Pair is comprised of a reference scene and a secondary scene. These scenes typically intersect geographically,
    but that is not a requirement. When a pair is created, its perpendicular and temporal baselines are calculated
    and stored in the self.perpendicular and self.temporal member variables.

    Two pairs are equivalent if they have matching reference and secondary dates
    """
    def __init__(self, ref: ASFProduct, sec: ASFProduct):
        self.ref = ref
        self.sec = sec

        self.perpendicular = calculate_perpendicular_baselines(
            ref.properties['sceneName'], 
            [sec, ref])[0].properties['perpendicularBaseline']

        ref_time = parse_datetime(ref.properties["startTime"])
        if ref_time.tzinfo is None:
            ref_time = pytz.utc.localize(ref_time)
        sec_time = parse_datetime(sec.properties["startTime"])
        if sec_time.tzinfo is None:
            sec_time = pytz.utc.localize(sec_time)

        self.ref_date = ref_time.date()
        self.sec_date = sec_time.date()
        self.temporal = self.sec_date - self.ref_date

        # warn user if they lack optional dependency needed for estimate_s1_mean_coherence
        if importlib.util.find_spec("xarray") is None:
            msg = (
                "Warning: Pair.estimate_s1_mean_coherence() requires xarray as a dependency"
                "However, your Pair is still available without access to coherence estimation."
            )
            warnings.warn(OptionalDependencyWarning(msg))

    def __repr__(self) -> str:
        return f"Pair({self.ref_date}, {self.sec_date})"

    def __eq__(self, other):
        if not isinstance(other, Pair):
            return NotImplemented
        return (self.ref_date == other.ref_date and
                self.sec_date == other.sec_date)

    def __hash__(self) -> int:
        return hash((self.ref.date.date(), self.sec.date.date()))

    def estimate_s1_mean_coherence(self) -> float:
        '''
        Estimates mean coherence for a Pair of Sentinel-1 scenes or bursts using the 11367x4367 overview of the 2019-2020 
        VV COH data from the Global Seasonal Sentinel-1 Interferometric Coherence and Backscatter Dataset:
        https://asf.alaska.edu/datasets/daac/global-seasonal-sentinel-1-interferometric-coherence-and-backscatter-dataset/

        To support effecient in-place subsetting and access, the VV COH data has been saved to a public Zarr Store in AWS S3:
        s3://asf-search-coh/global_coh_100ppd_11367x4367

        Returns:
        '''
        import xarray as xr

        month = parse_datetime(self.ref.properties["startTime"]).month
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
            msg = (f"""Coherence dataset includes temporal baselines up to 48 days.
                   Temporal baseline: {self.temporal.days} days""")
            raise CoherenceEstimationError(msg)

        uri = f"s3://asf-search-coh/global_coh_100ppd_11367x4367/Global_{season}_vv_COH{temporal}_100ppd.zarr"
        coords = self.ref.geometry['coordinates'][0]
        lons, lats = zip(*coords)
        minx, miny, maxx, maxy = min(lons), min(lats), max(lons), max(lats)

        ds = xr.open_zarr(
            uri,
            consolidated=True
            )
        ds = ds.rio.write_crs("EPSG:4326", inplace=False)
        subset = ds.rio.clip_box(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
        return subset.coherence.mean().compute().item()

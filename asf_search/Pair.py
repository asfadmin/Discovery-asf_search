import importlib.util
import math

from .ASFProduct import ASFProduct
from .baseline import calculate_perpendicular_baselines
from .exceptions import CoherenceEstimationError
import pytz

_COHERENCE_OPT_DEPS = ['zarr', 's3fs', 'rioxarray', 'xarray']
try:
    for spec in _COHERENCE_OPT_DEPS:
        if importlib.util.find_spec(spec) is None:
            raise ImportError

    import fsspec
    import xarray as xr

except ImportError:
    fsspec = None
    xr = None

try:
    from ciso8601 import parse_datetime
except ImportError:
    from dateutil.parser import parse as parse_datetime


class Pair:
    """
    A Pair is comprised of a reference scene and a secondary scene. These scenes typically intersect geographically,
    but that is not a requirement. When a pair is created, its perpendicular and temporal baselines are calculated
    and stored in the self.perpendicular_baseline and self.temporal_baseline member variables.

    Two pairs are equivalent if they have matching reference and secondary dates
    """
    def __init__(self, ref: ASFProduct, sec: ASFProduct):
        self.ref = ref
        self.sec = sec
        self.id = (ref.properties['sceneName'], sec.properties['sceneName'])

        self.perpendicular_baseline = calculate_perpendicular_baselines(
            ref.properties['sceneName'], 
            [sec, ref])[0].properties['perpendicularBaseline']

        self.ref_time = parse_datetime(ref.properties["startTime"])
        if self.ref_time.tzinfo is None:
            self.ref_time = pytz.utc.localize(self.ref_time)
        self.sec_time = parse_datetime(sec.properties["startTime"])
        if self.sec_time.tzinfo is None:
            self.sec_time = pytz.utc.localize(self.sec_time)

        self.temporal_baseline = self.sec_time.date() - self.ref_time.date()

    def __repr__(self) -> str:
        return f"Pair({self.id[0]}, {self.id[1]})"

    def __eq__(self, other):
        if not isinstance(other, Pair):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def estimate_s1_mean_coherence(self) -> float:
        '''
        Estimates mean coherence for a Pair of Sentinel-1 scenes or bursts using the 11367x4367 overview of the 2019-2020 
        VV COH data from the Global Seasonal Sentinel-1 Interferometric Coherence and Backscatter Dataset:
        https://asf.alaska.edu/datasets/daac/global-seasonal-sentinel-1-interferometric-coherence-and-backscatter-dataset/

        To support effecient in-place subsetting and access, the VV COH data has been saved to a public Zarr Store in AWS S3:
        s3://asf-search-coh/global_coh_100ppd_11367x4367

        Returns:
        '''
        if xr is None or fsspec is None:
            raise ImportError(
                'The `estimate_s1_mean_coherence()` method requires the optional asf-search '
                f'dependencies {_COHERENCE_OPT_DEPS}, '
                'but they could not be found in the current python environment. '
                'Enable this method by including the appropriate pip or conda install. '
                'Ex: `python -m pip install asf-search[coherence]`'
            )

        month = parse_datetime(self.ref.properties["startTime"]).month
        if month in [12, 1, 2]:
            season = 'winter'
        elif month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        elif month in [9, 10, 11]:
            season = 'fall'

        temporal = math.ceil(self.temporal_baseline.days / 6) * 6
        if temporal > 48:
            msg = (f"""Coherence dataset includes temporal baselines up to 48 days.
                   Temporal baseline: {self.temporal_baseline.days} days""")
            raise CoherenceEstimationError(msg)

        uri = f"s3://asf-search-coh/global_coh_100ppd_11367x4367_Zarrv2/Global_{season}_vv_COH{temporal}_100ppd.zarr"
        coords = self.ref.geometry['coordinates'][0]
        lons, lats = zip(*coords)
        minx, miny, maxx, maxy = min(lons), min(lats), max(lons), max(lats)

        ds = xr.open_zarr(
            fsspec.get_mapper(uri, s3={'anon': True}),
            consolidated=False
            )
        ds = ds.rio.write_crs("EPSG:4326", inplace=False)
        subset = ds.rio.clip_box(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
        return subset.coherence.mean().compute().item()

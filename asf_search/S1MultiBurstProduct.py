from dataclasses import dataclass
from datetime import timedelta
import importlib.util
from typing import List, Literal

from asf_search import ASF_LOGGER
from .ASFProduct import ASFProduct
from .search import geo_search

try:
    from ciso8601 import parse_datetime
except ImportError:
    from dateutil.parser import parse as parse_datetime

_SBASNETWORK_S1_MULTIBURST_OPT_DEPS = ['burst2safe']
try:
    for spec in _SBASNETWORK_S1_MULTIBURST_OPT_DEPS:
        if importlib.util.find_spec(spec) is None:
            raise ImportError
    from burst2safe.safe import Safe
    from burst2safe.utils import BurstInfo
except ImportError:
    Safe = None
    BurstInfo = None

Subswath = Literal["IW1", "IW2", "IW3"]


@dataclass(frozen=True)
class S1MultiBurst:
    """
    Represents a Sentinel-1 burst and which subswaths it should include.
    """
    relative_burst_id: str
    subswaths: tuple[Subswath, ...]


@dataclass(frozen=True)
class S1MultiBurstGroup:
    """
    Represents a group of S1MultiBursts to be processed together.
    """
    bursts: list[S1MultiBurst]

    def __post_init__(self):
        self.check_group_validity()

    # Temporarily borrowed (edited) from burst2safe, until validation logic moves to its own package.
    # https://github.com/ASFHyP3/burst2safe/blob/develop/src/burst2safe/safe.py#L83
    def check_group_validity(self) -> None:
        """Check that the burst group is valid.

        A valid burst group must:
        - Have the same acquisition mode
        - Be from the same absolute orbit
        - Be contiguous in time and space

        Args:
            burst_infos: A list of BurstInfo objects
        """

        swaths = sorted(list(set([int(subswath[2]) for burst in self.bursts for subswath in burst.subswaths])))

        burst_range: dict[str, tuple[int, int]] = {}
        for swath in swaths:
            burst_subset = [burst for burst in self.bursts if f"IW{swath}" in burst.subswaths]


            if not burst_subset:
                burst_range[swath] = (0, 0)
                continue

            self.check_burst_group_validity(burst_subset, swath)

            burst_ids = [int(info.relative_burst_id.split("_")[1]) for info in burst_subset]
            burst_range[swath] = (min(burst_ids), max(burst_ids))

        if len(swaths) <= 1:
            return

        for swath1, swath2 in zip(swaths, swaths[1:]):
            min_diff = burst_range[swath1][0] - burst_range[swath2][0]
            if abs(min_diff) > 1:
                raise ValueError(f'Products from swaths {swath1} and {swath2} do not overlap')

            max_diff = burst_range[swath1][1] - burst_range[swath2][1]
            if abs(max_diff) > 1:
                raise ValueError(f'Products from swaths {swath1} and {swath2} do not overlap')
            

    # Temporarily borrowed (edited) from burst2safe, until validation logic moves to its own package.
    # https://github.com/ASFHyP3/burst2safe/blob/develop/src/burst2safe/swath.py#L63            
    def check_burst_group_validity(self, burst_subset, swath):
        """Check that the burst group is valid.

        The burst group must:
        - Not contain duplicate granules
        - Have the same absolute orbit
        - Have consecutive burst IDs

        Args:
            burst_infos: A list of BurstInfo objects
        """
        granules = [f"{burst.relative_burst_id}_IW{swath}" for burst in burst_subset]

        duplicates = list(set([x for x in granules if granules.count(x) > 1]))
        if duplicates:
            raise ValueError(f'Found duplicate granules: {duplicates}.')

        orbits = set([granule.split("_")[0] for granule in granules])
        if len(orbits) != 1:
            raise ValueError(f'All bursts must have the same absolute orbit. Found: {orbits}.')

        burst_ids = [int(burst.split('_')[1]) for burst in granules]
        burst_ids.sort()
        if burst_ids != list(range(min(burst_ids), max(burst_ids) + 1)):
            raise ValueError(f'All bursts must have consecutive burst IDs. Found: {burst_ids}.')


class S1MultiBurstProduct():

    def __init__(
        self,
        multiburst_group: S1MultiBurstGroup = None,
        start_date: str = None,
        geo_reference_bursts: List[ASFProduct] = None   
    ):
        self.start_date=start_date
        if not multiburst_group and not geo_reference_bursts:
            raise ValueError("Provide multiburst_group or geo_reference_bursts")
        
        if not geo_reference_bursts:
            self.geo_reference_bursts = self.identify_geo_reference_bursts(multiburst_group)
        else:
            self.geo_reference_bursts = geo_reference_bursts

        if not multiburst_group:
            self.multiburst_group = self.identify_multiburst_group(geo_reference_bursts)
        else:
            self.multiburst_group = multiburst_group

        start_time = max([p.properties["startTime"] for p in self.geo_reference_bursts])
        stop_time = max([p.properties["stopTime"] for p in self.geo_reference_bursts])
        self.id = self._build_scene_name(start_time)
        self.properties = {
            "sceneName": self.id,
            "startTime": start_time,
            "stopTime": stop_time,
        }

    def __repr__(self) -> str:
        return f"S1MultiBurstProduct({self.id})"

    def __eq__(self, other):
        if not isinstance(other, S1MultiBurstProduct):
            return NotImplemented
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)

    def __len__(self):
        return len(self.geo_reference_bursts)

    def identify_geo_reference_bursts(self, multiburst_group) -> List[ASFProduct]:
        """
        Searches for a geographic reference scene for each burst. Provides
        the earliest acquisition within the temporal bounds of the S1MultiBurstSBASNetwork.

        Returns a list of ASFProducts as geographic reference scenes.
        """
        relative_burst_ids = [f"{burst.relative_burst_id}_{swath}" 
                              for burst in multiburst_group.bursts
                              for swath in burst.subswaths]

        results = geo_search(
            fullBurstID=relative_burst_ids, 
            start=self.start_date, 
            end=str((parse_datetime(self.start_date) + timedelta(days=48)).date()),
            )
        return [min([r for r in results if r.properties['burst']['fullBurstID'] == b], key=lambda obj: obj.properties['startTime']) for b in relative_burst_ids]

    def identify_multiburst_group(self, geo_reference_bursts):
        relative_burst_ids = set([f'{p.properties["pathNumber"]}_{p.properties["burst"]["relativeBurstID"]}' for p in geo_reference_bursts])
        burst_group_dict = {burst_id: [] for burst_id in relative_burst_ids}
        for p in geo_reference_bursts:
            burst_id = f'{p.properties["pathNumber"]}_{p.properties["burst"]["relativeBurstID"]}'
            burst_group_dict[burst_id].append(p.properties["burst"]["subswath"])

        multibursts = [S1MultiBurst(k, v) for k, v in burst_group_dict.items()]
        return S1MultiBurstGroup(bursts=multibursts)
    
    def _build_scene_name(self, start_time):
        start_time = "".join(start_time.split("T")[0].split("-"))
        id = ""
        for multiburst in self.multiburst_group.bursts:
            id = f"{id}_{multiburst.relative_burst_id}_IW"
            for subswath in multiburst.subswaths:
                id = f"{id}{subswath[2]}"
        return f"{id[1:]}_{start_time}"
import copy
from dataclasses import dataclass
from datetime import timedelta
import importlib.util
from typing import List, Optional, Tuple, Literal

from asf_search import ASF_LOGGER
from .Pair import Pair
from .SBASNetwork import SBASNetwork
from .ASFSearchOptions import ASFSearchOptions
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


Swath = Literal["IW1", "IW2", "IW3"]
RelativeBurstID = str

@dataclass(frozen=True)
class S1MultiBurstGroup:
    """
    Represents a group of Sentinel-1 bursts and swaths to be processed together.

    Example:
    S1MultiBurstGroup(
        bursts={
        "173_370305": ("IW1", "IW2", "IW3"),
        "173_370306": ("IW1", "IW2", "IW3"),
        "173_370307": ("IW1", "IW2", "IW3")
        }
    )   
    """
    bursts: dict[RelativeBurstID, tuple[Swath, ...]]

    def __post_init__(self):
        if BurstInfo is None or Safe is None:
            raise ImportError(
                'The `S1MultiBurstGroup` class requires the optional asf-search '
                f'dependency {_SBASNETWORK_S1_MULTIBURST_OPT_DEPS}, '
                'but it could not be found in the current python environment. '
                'Enable this method by including the appropriate pip or conda install. '
                'Ex: `python -m pip install asf-search[sbasnetwork_s1_multiburst]`'
            )
        self._check_validity()

    def _check_validity(self):
        burst_infos = [
            BurstInfo(
                granule=f"{k}_{swath}",
                slc_granule=None,
                swath=swath,
                polarization="",
                burst_id=int(k.split('_')[1]),
                burst_index=0,
                direction="",
                absolute_orbit=0,
                relative_orbit=int(k.split('_')[0]),
                date=None,
                data_url="",
                data_path=None,
                metadata_url=None,
                metadata_path=None,
            )
            for k, swaths in self.bursts.items()
            for swath in swaths
        ]

        Safe.check_group_validity(burst_infos)


@dataclass(frozen=True)
class S1MultiBurstSBASPairMap:
    """
    A dictionary of 
    {
        geo_reference_burst_1: [Pair_1, Pair_2],
        geo_reference_burst_2: [Pair_3, Pair_4],
        geo_reference_burst_3: [Pair_5, Pair_6],
    }

    or 

    `geo_reference_dict` must map each burst SBASNetwork's geo_reference scene 
    to the pairs that should be added or restored to that specific network.
    """
    pairs_by_geo_reference: dict[str, list[Pair]]
    sbas_networks: list[SBASNetwork]

    def __post_init__(self):
        self._check_validity()

    def _check_validity(self):
        geo_reference_list = [sbas.geo_reference for sbas in self.sbas_networks]
        if geo_reference_list != list(self.pairs_by_geo_reference.keys()):
            raise Exception(
                "geo_reference_dict must have keys corresponding to each multiburst SBASNetwork geo_reference product\n"
                f"geo_reference_dict.keys(): {self.pairs_by_geo_reference.keys()}\n"
                f"self.sbas_networks geo_reference scenes: {geo_reference_list}"
                )
        
        if len(set([len(i) for i in list(self.pairs_by_geo_reference.values())])) > 1:
            raise Exception("All pair lists in geo_reference_dict must be of equal length")

        for geo_ref, pair_list in self.pairs_by_geo_reference.items():
            geo_ref_full_burst_id = geo_ref.properties["burst"]["fullBurstID"]
            for pair in pair_list:
                ref_full_burst_id = pair.ref.properties["burst"]["fullBurstID"]
                sec_full_burst_id = pair.sec.properties["burst"]["fullBurstID"]
                if geo_ref_full_burst_id != ref_full_burst_id or geo_ref_full_burst_id != sec_full_burst_id:
                    raise Exception(f"Pair {pair}'s reference or secondary full burst ID does not match burst SBASNetwork's geo_reference scene's full burst ID ({geo_ref_full_burst_id}).")


class S1MultiBurstSBASNetwork():
    """
    The S1MultiBurstSBASNetwork is used for generating SBASNetworks for groups of Sentinel-1 bursts.

    Burst groups are passed to the constructor as validated S1MultiBurstGroup objects. Geographic 
    reference scenes are found for each burst in the group. An SBASNetwork is generated from each
    geographic reference scene and stored in the sbas_networks member variable. 
    
    Cooresponding Pairs are guaranteed for every SBASNetwork in sbas_networks. If a Pair is not 
    represented in every burst SBASNetwork, it is removed from them all.
    """
    def __init__( 
        self,
        multiburst_group: S1MultiBurstGroup,
        start_date: str = None,
        end_date: str = None,
        season: Tuple[int] = (1, 365),
        perpendicular_baseline: Optional[int] = 400,
        inseason_temporal_baseline: Optional[int] = 36,
        bridge_year_threshold: Optional[int] = 1,
        bridge_target_date: Optional[str] = None,
        opts: Optional[ASFSearchOptions] = ASFSearchOptions(),
        allow_missing_state_vectors: Optional[bool] = False
    ):

        self.start_date=start_date
        self.end_date=end_date
        self.season=season
        self.bridge_target_date=bridge_target_date
        self.perpendicular_baseline=perpendicular_baseline
        self.inseason_temporal_baseline=inseason_temporal_baseline
        self.bridge_year_threshold=bridge_year_threshold
        self.opts=opts
        self.allow_missing_state_vectors=allow_missing_state_vectors
        
        self.multiburst_group = multiburst_group
        self.georeferences = self.define_geo_references()

        self.sbas_networks = [SBASNetwork(
            geo_reference, 
            start_date=self.start_date,
            end_date=self.end_date,
            season=self.season,
            perpendicular_baseline=self.perpendicular_baseline,
            inseason_temporal_baseline=self.inseason_temporal_baseline,
            bridge_year_threshold=self.bridge_year_threshold,
            bridge_target_date=self.bridge_target_date,
            opts=copy.deepcopy(self.opts),
            allow_missing_state_vectors=self.allow_missing_state_vectors
            ) for geo_reference in self.georeferences]
        
        # update georeferences from results of stack searches performed when creating self.sbas_networks
        self.georeferences = [network.geo_reference for network in self.sbas_networks]

        removed_pairs = self.reconcile_sbasnetworks()
        if len(removed_pairs) > 0:
            ASF_LOGGER.info(f"Removed Pairs with the following dates due to a lack of coverage across all S1 multiburst SBASNetworks: {removed_pairs}")

    def remove_pairs(self, geo_reference_dict: S1MultiBurstSBASPairMap):
        """
        Remove pairs with matching ref/sec dates from all burst SBASNetworks.
        """
        for sbas in self.sbas_networks:
            sbas.remove_pairs(geo_reference_dict.pairs_by_geo_reference[sbas.geo_reference])
        

    def add_pairs(self, geo_reference_dict: S1MultiBurstSBASPairMap):
        """
        Add explicit pairs to each burst SBASNetwork.

        {
            geo_reference_burst_1: [Pair_1, Pair_2],
            geo_reference_burst_2: [Pair_3, Pair_4],
            geo_reference_burst_3: [Pair_5, Pair_6],
        }

        `geo_reference_dict` must map each burst SBASNetwork's geo_reference scene 
        to the pairs that should be added or restored to that specific network.
        """

        for sbas in self.sbas_networks:
            sbas.add_pairs(geo_reference_dict.pairs_by_geo_reference[sbas.geo_reference])


    def reconcile_sbasnetworks(self) -> List[List[Pair]]:
        """
        Confirms that each SBASNetwork in sbas_networks contains corresponding date
        Pairs. If a date pair is not represented in every SBASNetwork, it is
        removed from them all.

        Returns: A list of lists of all Pairs that were removed
        """
        network_date_pairs = [
            {
                (pair.ref_time.date(), pair.sec_time.date())
                for pair in network.subset_stack
            }
            for network in self.sbas_networks
        ]

        common_date_pairs = set.intersection(*network_date_pairs)

        pairs_to_remove_list = []
        for network in self.sbas_networks:
            pairs_to_remove = [
                pair
                for pair in network.subset_stack
                if (pair.ref_time.date(), pair.sec_time.date()) not in common_date_pairs
            ]
            if len(pairs_to_remove) > 0:
                network.remove_pairs(pairs_to_remove)
                pairs_to_remove_list.append(pairs_to_remove)

        return pairs_to_remove_list


    def define_geo_references(self) -> List[ASFProduct]:
        """
        Searches for a geographic reference scene for each burst. Provides
        the earliest acquisition within the temporal bounds of the S1MultiBurstSBASNetwork.

        Returns a list of ASFProducts as geographic reference scenes.
        """
        relative_burst_ids = [f"{k}_{swath}" for k, v in self.multiburst_group.bursts.items() for swath in v]
        results = geo_search(
            fullBurstID=relative_burst_ids, 
            start=self.start_date, 
            end=str((parse_datetime(self.start_date) + timedelta(days=48)).date()),
            season=self.season, 
            opts=self.opts
            )
        return [min([r for r in results if r.properties['burst']['fullBurstID'] == b], key=lambda obj: obj.properties['startTime']) for b in relative_burst_ids]
    

    def get_scene_ids(self) -> List[List[Tuple[str]]]: 
        """
        This is a convenience method to support ordering INSAR_ISCE_MULTI_BURST jobs from
        HyP3.

        Returns a list of lists of tuples of reference and secondary burst SLC IDs:
        [
            [(ref_burst_1_id, ref_burst_2_id), (sec_burst_1_id, sec_burst_2_id)],
            [(ref_burst_3_id, ref_burst_4_id), (sec_burst_3_id, sec_burst_4_id)],
        ]
        """     
        pair_ids = [s.get_scene_ids() for s in self.sbas_networks]
        multiburst_job_pair_ids = [list(x) for x in zip(*pair_ids)]
        return [list(zip(*pairs)) for pairs in multiburst_job_pair_ids]
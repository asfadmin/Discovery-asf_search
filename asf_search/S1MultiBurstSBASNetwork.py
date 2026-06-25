import copy
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
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


@dataclass(frozen=True)
class S1MultiBurst:
    """
    Represents a Sentinel-1 burst and which swaths it should include.
    """
    relative_burst_id: str
    swaths: tuple[Swath, ...]


@dataclass(frozen=True)
class S1MultiBurstGroup:
    """
    Represents a group of S1MultiBursts to be processed together.
    """
    bursts: list[S1MultiBurst]

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
                granule=f"{burst.relative_burst_id}_{swath}",
                slc_granule=None,
                swath=swath,
                polarization="",
                burst_id=int(burst.relative_burst_id.split('_')[1]),
                burst_index=0,
                direction="",
                absolute_orbit=0,
                relative_orbit=int(burst.relative_burst_id.split('_')[0]),
                date=None,
                data_url="",
                data_path=None,
                metadata_url=None,
                metadata_path=None,
            )
            for burst in self.bursts
            for swath in burst.swaths
        ]

        Safe.check_group_validity(burst_infos)

@dataclass(frozen=True)
class S1GeoReferenceBurstPairCollection:
    """
    Represents a Sentinel-1 geo_reference burst product for an
    SBASNetwork and a list of Sentinel-1 burst Pairs.

    A validity check is performed to ensure that all Pair scenes have a fullBurstID
    matching the fullBurstID of the geo_reference_burst
    """
    geo_reference_burst: ASFProduct
    pairs: tuple[Pair, ...]

    def __post_init__(self):
        self._check_validity()

    def _check_validity(self):   
        geo_ref_full_burst_id = self.geo_reference_burst.properties["burst"]["fullBurstID"]
        for pair in self.pairs:
            ref_full_burst_id = pair.ref.properties["burst"]["fullBurstID"]
            sec_full_burst_id = pair.sec.properties["burst"]["fullBurstID"]
            if geo_ref_full_burst_id != ref_full_burst_id or geo_ref_full_burst_id != sec_full_burst_id:
                raise Exception(f"Pair {pair}'s reference or secondary fullBurstID does not match burst SBASNetwork's geo_reference_burst's fullBurstID ({geo_ref_full_burst_id}).")

class PairList(Enum):
    FULL = "full_stack"
    SUBSET = "subset_stack"
    REMOVE = "remove_list"
    CONNECTED = "connected_substacks"


@dataclass(frozen=True)
class S1MultiBurstSBASDelta:
    """
    Represents a change set to be applied to a collection of SBASNetworks (typically to S1MultiBurstSBASNetwork.sbas_networks).
    It is used to define Pairs to be removed from or added to S1MultiBurstSBASNetwork.sbas_networks.subset_stack.

    The delta is composed of one S1GeoReferenceBurstPairCollection per
    SBASNetwork. Each collection associates a geo-reference burst with the
    Pairs that should be added to or removed from the corresponding
    SBASNetwork's subset_stack.

    A validity check is performed to ensure that:
    - All S1GeoReferenceBurstPairCollection.geo_reference_bursts correspond to the geo_reference product of an
     SBASNetwork in sbas_networks
    - The ordering of pair_collections matches the ordering of `sbas_networks.
    - All S1GeoReferenceBurstPairCollections contain the same number of Pairs

    Internally, pair_collections are indexed by geo-reference burst to support efficient lookup when applying the delta to SBASNetworks.
    """
    pair_collections: tuple[S1GeoReferenceBurstPairCollection, ...]
    sbas_networks: list[SBASNetwork]

    def __post_init__(self):
        self._check_validity()

        object.__setattr__(
            self,
            "_pair_collections",
            {
                collection.geo_reference_burst: collection.pairs
                for collection in self.pair_collections
            },
        )

    def _check_validity(self):
        geo_references = [sbas.geo_reference for sbas in self.sbas_networks]
        collection_geo_references = [
            collection.geo_reference_burst
            for collection in self.pair_collections
        ]

        if geo_references != collection_geo_references:
            raise Exception(
                "pair collections must correspond to each multiburst SBASNetwork geo_reference product\n"
                f"pair collection geo_references: {collection_geo_references}\n"
                f"sbas_networks geo_references: {geo_references}"
            )

        if len({len(collection.pairs) for collection in self.pair_collections}) > 1:
            raise Exception("All pair collections must contain the same number of pairs")

    def pairs_for(self, geo_reference: ASFProduct) -> tuple[Pair, ...]:
        return self._pair_collections[geo_reference]

class S1MultiBurstSBASNetwork():
    """
    The S1MultiBurstSBASNetwork is used for generating SBASNetworks for groups of Sentinel-1 bursts.

    Burst groups are passed to the constructor as validated S1MultiBurstGroup objects. Geographic 
    reference scenes are found for each burst in the group. An SBASNetwork is generated from each
    geographic reference scene and stored in the sbas_networks member variable. 
    
    Cooresponding Pairs are guaranteed for every SBASNetwork in sbas_networks. If a Pair is not 
    represented in every burst SBASNetwork, it is removed from them all.
    """

    @property
    def scene_ids(self) -> List[List[Tuple[str, str]]]:
        """
        This is a convenience property to support ordering INSAR_ISCE_MULTI_BURST jobs from
        HyP3.

        Provides the scene IDs for the largest connected network for each SBASNetwork in sbas_networks

        Use the get_scene_ids method to get the IDs for other pair lists (full_stack, subset_stack, 
        any network in connected_substacks, or remove_list)

        Returns a list of lists of tuples of reference and secondary burst SLC IDs:
        [
            [(ref_burst_1_id, ref_burst_2_id), (sec_burst_1_id, sec_burst_2_id)],
            [(ref_burst_3_id, ref_burst_4_id), (sec_burst_3_id, sec_burst_4_id)],
        ]
        """     
        pair_ids = [s.scene_ids for s in self.sbas_networks]
        multiburst_job_pair_ids = zip(*pair_ids)
        return [list(zip(*pairs)) for pairs in multiburst_job_pair_ids]
    

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
        self.geo_references = self.define_geo_references()

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
            ) for geo_reference in self.geo_references]
        
        # update geo_references from results of stack searches performed when creating self.sbas_networks
        self.geo_references = [network.geo_reference for network in self.sbas_networks]

        removed_pairs = self.reconcile_sbasnetworks()
        if len(removed_pairs) > 0:
            ASF_LOGGER.info(f"Removed Pairs with the following dates due to a lack of coverage across all S1 multiburst SBASNetworks: {removed_pairs}")


    def remove_pairs(self, multiburst_delta: S1MultiBurstSBASDelta):
        """
        Remove pairs in multiburst_delta from all S1MultiBurstSBASNetwork.sbas_networks.
        """
        for sbas in self.sbas_networks:
            sbas.remove_pairs(multiburst_delta.pairs_for(sbas.geo_reference))
        

    def add_pairs(self, multiburst_delta: S1MultiBurstSBASDelta):
        """
        Add pairs in multiburst_delta to all S1MultiBurstSBASNetwork.sbas_networks.
        """

        for sbas in self.sbas_networks:
            sbas.add_pairs(multiburst_delta.pairs_for(sbas.geo_reference))


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
        relative_burst_ids = [f"{burst.relative_burst_id}_{swath}" 
                              for burst in self.multiburst_group.bursts
                              for swath in burst.swaths]

        results = geo_search(
            fullBurstID=relative_burst_ids, 
            start=self.start_date, 
            end=str((parse_datetime(self.start_date) + timedelta(days=48)).date()),
            season=self.season, 
            opts=self.opts
            )
        return [min([r for r in results if r.properties['burst']['fullBurstID'] == b], key=lambda obj: obj.properties['startTime']) for b in relative_burst_ids]


    def get_scene_ids(
            self, 
            pair_list: Optional[PairList] = None,
            connected_substack_index: Optional[int] = None
            ) -> List[List[Tuple[str, str]]]:
        """
        This is a convenience method to support ordering INSAR_ISCE_MULTI_BURST jobs from HyP3.

        Defaults to providing the scene IDs for the largest connected network for each SBASNetwork in sbas_networks.

        pair_list (optional): A PairList describing the pair_list in each SBASNetwork for which to retrieve scene IDs
        connected_substack_index (optional): If PairList.CONNECTED is used, provides the index of the pair list in connected_substacks

        Returns a list of lists of tuples of reference and secondary burst SLC IDs:
        [
            [(ref_burst_1_id, ref_burst_2_id), (sec_burst_1_id, sec_burst_2_id)],
            [(ref_burst_3_id, ref_burst_4_id), (sec_burst_3_id, sec_burst_4_id)],
        ]
        """
        if not pair_list or (pair_list is PairList.CONNECTED and connected_substack_index is None):
            return self.scene_ids
        elif pair_list is PairList.SUBSET:
            pair_ids = [s.get_scene_ids(s.subset_stack) for s in self.sbas_networks]
        elif pair_list is PairList.FULL:
            pair_ids = [s.get_scene_ids(s.full_stack) for s in self.sbas_networks]
        elif pair_list is PairList.REMOVE:
            pair_ids = [s.get_scene_ids(s.remove_list) for s in self.sbas_networks]
        elif pair_list is PairList.CONNECTED:
            pair_ids = [s.get_scene_ids(s.connected_substacks[connected_substack_index]) for s in self.sbas_networks]

        multiburst_job_pair_ids = zip(*pair_ids)
        return [list(zip(*pairs)) for pairs in multiburst_job_pair_ids]
from collections import defaultdict, deque
from copy import copy
from datetime import datetime, date
from typing import Optional, List, Tuple, Dict
import warnings

from .ASFProduct import ASFProduct
from .Pair import Pair
from .ASFSearchOptions import ASFSearchOptions
from .warnings import PairNotInFullStackWarning
import numpy as np
import pandas as pd

try:
    from ciso8601 import parse_datetime
except ImportError:
    from dateutil.parser import parse as parse_datetime

date_like = str | date | datetime | pd.Timestamp


class Stack:
    """
    A Stack contains collections of Pairs

    Stack objects contain several stacks as member variables, which are lists of Pair objects.
    
    member stacks:
    - self.full_stack: Every possible pair based on the provided geo_reference scene 
    and ASFSearchOptions.
    - self.subset_stack: The (possibly disconnected) SBAS stack
    - self.connected_substacks: A list containing each disconnected component of self.subset_stack

    self._remove_list is a list of date pair tuples that is used for filtering a subset_stack from a full_stack
    """
    def __init__(
        self,
        geo_reference: ASFProduct,
        temporal_baseline: Optional[int] = None,
        opts: Optional[ASFSearchOptions] = None
    ):
        self.geo_reference = geo_reference
        self.temporal_baseline = temporal_baseline
        if opts is None:
            opts = ASFSearchOptions()
        self.opts = opts
        self.full_stack = self._build_full_stack()
        self._remove_list = []
        self.subset_stack = self._get_subset_stack()
        self.connected_substacks = self._find_connected_substacks()

    @property
    def remove_list(self) -> List[Tuple[date, date]]:
        """
        Return a copy of self._remove_list so client changes 
        do not alter self._remove_list without a stack update

        Disallow: 
          - my_stack.remove_list.append(my_pair)
          - my_stack.remove_list.remove(my_pair)

        Support:
          - my_stack.remove_pairs([my_pair, some_other_pair, ...])
          - my_stack.add_pairs([my_pair, some_other_pair, ...])
        """
        return copy(self._remove_list)

    @remove_list.setter
    def remove_list(self, pairs: List[Pair]):
        """
        Accept date pair tuples as datetime.datetime, datetime.date, 
        pandas.Timestamp, or ISO datetime string.

        Return tuples of datetime.date
        """
        # remove duplicates
        self._remove_list = list(set(pairs))
        self._update_stack()

    def remove_pairs(self, pairs: List[Pair]):
        """
        Remove pairs from self.subset_stack, 
        i.e., add them to self._remove_list
        """
        for pair in pairs:
            if pair not in self._remove_list:
                if pair in self.full_stack:
                    self._remove_list.append(pair)
                else:
                    msg = f"warning: {pair} is not in full_stack"
                    warnings.warn(PairNotInFullStackWarning(msg))
        self._update_stack()

    def add_pairs(self, pairs: List[Pair]):
        """
        Add pairs to self.subset_stack and, if necessary, to self.full_stack 
        i.e., remove them from self._remove_list if present
              or else add them to self.full_stack 

        This allows for the addition of custom pairs that were not originally present
        in self.full_stack
        """
        for pair in pairs:
            if pair in self._remove_list:
                self._remove_list.remove(pair)
            else:
                self.full_stack.append(pair)
        self._update_stack()

    def generate_pairs_within_baseline(self, dates):
        dates = sorted(dates)
        return [
            (dates[i], dates[j])
            for i in range(len(dates))
            for j in range(i + 1, len(dates))
            if (dates[j] - dates[i]).days <= self.temporal_baseline
        ]

    def _build_full_stack(self) -> List[Pair]:
        """
        Create self._full_stack, which involves performing a stack search
        of the georeference scene and creating a list of every possible Pair
        in which both products contain StateVectors and have a temporal baseline
        <=  self.temporal_baseline
        """
        geo_ref_stack = self.geo_reference.stack(opts=self.opts)
        return [
            Pair(p1, p2)
            for i, p1 in enumerate(geo_ref_stack)
            for p2 in geo_ref_stack[i+1:]
            if self.temporal_baseline is None
            or 
            (
                (parse_datetime(p2.properties['stopTime']) - parse_datetime(p1.properties['stopTime'])).days <= self.temporal_baseline
                and
                p1.baseline.get("noStateVectors")
                and
                p2.baseline.get("noStateVectors")
            )
        ]

    def _get_subset_stack(self) -> List[Pair]:
        """
        Create a subset_stack by removing every pair in
        self.remove_list from self.full_stack
        """
        return [pair for pair in self.full_stack if pair not in self.remove_list]

    def _update_stack(self):
        """
        Recalculate self.subset_stack and find its connected substacks.
        These two things should always happen together
        """
        self.subset_stack = self._get_subset_stack()
        self.connected_substacks = self._find_connected_substacks()


    def _find_connected_substacks(self) -> List[Dict[Tuple[date, date], Pair]]:
        """
        BFS to find all connected components of self.subset_stack
        """

        graph = defaultdict(list)
        for pair in self.subset_stack:
            graph[pair.ref].append(pair.sec)
            graph[pair.sec].append(pair.ref)

        visited_nodes = set()
        visited_pairs = set()
        components = []

        for node in graph:
            if node not in visited_nodes:
                component_nodes = set()
                component_pairs = {}

                queue = deque([node])
                visited_nodes.add(node)

                while queue:
                    current = queue.popleft()
                    component_nodes.add(current)

                    for neighbor in graph[current]:
                        if (current, neighbor) not in visited_pairs and (neighbor, current) not in visited_pairs:
                            for pair in self.subset_stack:
                                if (pair.ref == current and pair.sec == neighbor) or \
                                    (pair.sec == current and pair.ref == neighbor):
                                    component_pairs[Pair(pair.ref, pair.sec)] = pair
                                    break
                            visited_pairs.add((current, neighbor))
                            visited_pairs.add((neighbor, current))

                        if neighbor not in visited_nodes:
                            visited_nodes.add(neighbor)
                            queue.append(neighbor)

                components.append(component_pairs)

        return components

    def get_scene_ids(self, stack_list: Optional[List[Pair]] = None) -> List[Tuple[str, str]]:
        """
        Useful when ordering an SBAS stack from ASF HyP3 On-Demand Processing.
        Provides InSAR pair scene names in a list of tuples.

        If no stack_dict is passed, defaults to the largest connected substack

        Returns:
            A list tuples containing the reference and secondary scene name for each inSAR pair in the SBAS stack
        """
        if not stack_list:
            stack_list = max(self.connected_substacks, key=len)

        return [
            (pair.ref.properties["sceneName"], pair.sec.properties["sceneName"])
            for pair in stack_list
            ]
    
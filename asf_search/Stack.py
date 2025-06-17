from collections import defaultdict, deque
from copy import copy
from typing import Optional, List, Tuple, Dict
import warnings

from asf_search import ASFProduct, Pair
from asf_search.ASFSearchOptions import ASFSearchOptions
from datetime import datetime, date
import numpy as np
import pandas as pd

try:
    from ciso8601 import parse_datetime
except ImportError:
    from dateutil.parser import parse as parse_datetime

date_like = str | date | datetime | pd.Timestamp


class Stack:
    """
    A Stack contains collections of geographically overlapping Pairs

    Stack objects contain several stacks as member variables, which are dictionaries
    with tuples of datetime.dates as keys and cooresponding Pair objects as values.
    
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
    def remove_list(self, pairs: List[Tuple[date_like, date_like]]):
        """
        Accept date pair tuples as datetime.datetime, datetime.date, 
        pandas.Timestamp, or ISO datetime string.

        Return tuples of datetime.date
        """
        normalized = [self._normalize_pair(pair) for pair in pairs]
        # remove duplicates
        self._remove_list = list(set(normalized))
        self._update_stack()

    def remove_pairs(self, pairs: List[Tuple[date_like, date_like]]):
        """
        Remove pairs from self.subset_stack, 
        i.e., add them to self._remove_list
        """
        for pair in pairs:
            pair_dates = self._normalize_pair(pair)
            if pair_dates not in self._remove_list:
                if pair_dates in self.full_stack:
                    self._remove_list.append(pair_dates)
                else:
                    warnings.warn(
                        f"warning: {pair_dates} is not in Stack.full_stack",
                        UserWarning
                        )
        self._update_stack()

    def add_pairs(self, pairs: List[Tuple[date_like, date_like]]):
        """
        Add pairs to the subset_stack, 
        i.e., remove them from self._remove_list
        """
        for pair in pairs:
            pair_dates = self._normalize_pair(pair)
            if pair_dates in self._remove_list:
                if pair_dates in self.full_stack:
                    msg = (f"{pair_dates} is not part of full stack and cannot be added.\n"
                    f"Try creating a new Stack with search options that include it.\n"
                    f"Stack.ASFSearchOptions = {self.opts}")
                    warnings.warn(msg, UserWarning)
                self._remove_list.remove(pair_dates)
            else:
                raise warnings.warn(
                    f"warning: {pair_dates} is not present in Stack._remove_list", 
                    UserWarning
                    )
        self._update_stack()

    def _normalize_pair(self, pair: Tuple[date_like, date_like]) -> Tuple[date, date]:
        """
        convert date tuples from pandas.Timestamp, datetime.datetime,
        or iso formatted date string to tuples of datetime.date
        """
        def to_dt(val):
            if isinstance(val, pd.Timestamp):
                return val.to_pydatetime().date()
            elif isinstance(val, date):
                return val
            elif isinstance(val, datetime):
                return val.date()
            elif isinstance(val, np.datetime64):
                return val.astype(datetime)
            elif isinstance(val, str):
                return datetime.fromisoformat(val).date()
            else:
                raise Exception(f"Cannot handle date or timestamp of type: {type(val)}")
        return to_dt(pair[0]), to_dt(pair[1])

    def generate_pairs_within_baseline(self, dates):
        dates = sorted(dates)
        return [
            (dates[i], dates[j])
            for i in range(len(dates))
            for j in range(i + 1, len(dates))
            if (dates[j] - dates[i]).days <= self.temporal_baseline
        ]

    def _build_full_stack(self) -> Dict[Tuple[date, date], Pair]:
        """
        Create self._full_stack, which involves performing a stack search
        of the georeference scene and adding every possible date pair
        to a dict with tuples of datetime.dates as keys and cooresponding
        Pairs as values
        """
        geo_ref_stack = self.geo_reference.stack(opts=self.opts)
        dates = {parse_datetime(p.properties['stopTime']).date(): p for p in geo_ref_stack}
        date_pairs = {
            (d1, d2): (dates[d1], dates[d2])
            for i, d1 in enumerate(sorted(dates))
            for d2 in list(sorted(dates))[i + 1:]
            if self.temporal_baseline is None or (d2 - d1).days <= self.temporal_baseline
        }
        stack = {}
        for pair_dates, pair in date_pairs.items():
            if not pair[0].baseline.get("noStateVectors") and not pair[1].baseline.get("noStateVectors"):
                stack[(pair_dates[0], pair_dates[1])] = Pair(pair[0], pair[1])              
        return stack

    def _get_subset_stack(self) -> Dict[Tuple[date, date], Pair]:
        """
        Create a subset_stack by removing every pair in
        self.remove_list from self.full_stack
        """
        stack = {}
        for _, pair in self.full_stack.items():
            if (pair.ref_date, pair.sec_date) not in self.remove_list:
                stack[(pair.ref_date, pair.sec_date)] = pair
        return stack

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
        for pair in self.subset_stack.values():
            graph[pair.ref_date].append(pair.sec_date)
            graph[pair.sec_date].append(pair.ref_date)

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
                            for pair in self.subset_stack.values():
                                if (pair.ref_date == current and pair.sec_date == neighbor) or \
                                    (pair.sec_date == current and pair.ref_date == neighbor):
                                    component_pairs[(pair.ref_date, pair.sec_date)] = pair
                                    break
                            visited_pairs.add((current, neighbor))
                            visited_pairs.add((neighbor, current))

                        if neighbor not in visited_nodes:
                            visited_nodes.add(neighbor)
                            queue.append(neighbor)

                components.append(component_pairs)

        return components

    def get_insar_pair_ids(self, stack_dict: Optional[Dict[Tuple[date, date], Pair]] = None) -> List[Tuple[str, str]]:
        """
        Useful when ordering an SBAS stack from ASF HyP3 On-Demand Processing.
        Provides InSAR pair scene names in a list of tuples.

        If no stack_dict is passed, defaults to the largest connected substack

        Returns:
            A list tuples containing the reference and secondary scene name for each inSAR pair in the SBAS stack
        """
        if not stack_dict:
            stack_dict = max(self.connected_substacks, key=len)

        return [
            (pair.ref.properties["sceneName"], pair.sec.properties["sceneName"])
            for pair in stack_dict.values()
            ]

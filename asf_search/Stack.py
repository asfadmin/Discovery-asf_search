from collections import defaultdict, deque
import warnings

from asf_search import ASFProduct, Pair
from asf_search.ASFSearchOptions import ASFSearchOptions
from datetime import datetime, date
import pandas as pd

try:
    from ciso8601 import parse_datetime
except ImportError:
    from dateutil.parser import parse as parse_datetime

date_like = list[str | date | pd.Timestamp]


class Stack:
    def __init__(self, geo_reference: ASFProduct, opts: ASFSearchOptions = None):
        self.geo_reference = geo_reference
        self.opts = opts
        self.full_stack = self._build_full_stack()
        self._date_pair_remove_list = []
        self.subset_stack = self._get_subset_stack()
        self.connected_substacks = self._find_connected_substacks()
        
    @property
    def date_pair_remove_list(self) -> list[tuple[datetime, datetime]]:
        return self._date_pair_remove_list

    @date_pair_remove_list.setter
    def date_pair_remove_list(self, pairs: list[tuple[date_like, date_like]]):
        self._date_pair_remove_list = [self._normalize_pair(pair) for pair in pairs]
        self._update_stack()

    def remove_pairs(self, pairs: list[tuple[date_like, date_like]]):
        for pair in pairs:
            pair_dates = self._normalize_pair(pair)
            if pair_dates not in self._date_pair_remove_list:
                self._date_pair_remove_list.append(pair_dates)
        self._update_stack()

    def add_pairs(self, pairs: list[tuple[date_like, date_like]]):
        for pair in pairs:
            pair_dates = self._normalize_pair(pair)
            if pair_dates in self._date_pair_remove_list:
                self._date_pair_remove_list.remove(pair_dates)
            else:
                raise warnings.warn(
                    f"Warning: Cannot add {pair_dates} to subset_stack because it is not present in _date_pair_remove_list.", 
                    UserWarning
                    )
        self._update_stack()

    def _normalize_pair(self, pair: tuple[date_like, date_like]) -> tuple[datetime, datetime]:
        def to_dt(val):
            if isinstance(val, pd.Timestamp):
                return val.to_pydatetime().date()
            elif isinstance(val, date):
                return val
            elif isinstance(val, datetime):
                return val.date()
            else:
                return datetime.fromisoformat(val).date()
        return to_dt(pair[0]), to_dt(pair[1])

    def _build_full_stack(self) -> list[ASFProduct]:
        geo_ref_stack = self.geo_reference.stack(opts=self.opts)
        stack = {}
        for i, ref in enumerate(geo_ref_stack):
            for j, sec in enumerate(geo_ref_stack):
                if i < j and not ref.baseline.get("noStateVectors") and not sec.baseline.get("noStateVectors"):
                    pair = Pair(ref, sec)
                    stack[(pair.ref_date, pair.sec_date)] = pair
        return stack

    def _get_subset_stack(self):
        stack = {}
        for _, pair in self.full_stack.items():
            if (pair.ref_date, pair.sec_date) not in self.date_pair_remove_list:
                stack[(pair.ref_date, pair.sec_date)] = pair
        return stack

    def _update_stack(self):
        self.subset_stack = self._get_subset_stack()
        self.connected_substacks = self._find_connected_substacks()

    def _find_connected_substacks(self):
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


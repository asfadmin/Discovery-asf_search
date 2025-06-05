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

    @property
    def date_pair_remove_list(self) -> list[tuple[datetime, datetime]]:
        return self._date_pair_remove_list

    @date_pair_remove_list.setter
    def date_pair_cull_list(self, pairs: list[tuple[date_like, date_like]]):
        self._date_pair_remove_list = [self._normalize_pair(pair) for pair in pairs]
        self._get_subset_stack()

    def remove_pairs(self, pairs: list[tuple[date_like, date_like]]):
        for pair in pairs:
            self._date_pair_remove_list.append(self._normalize_pair(pair))
        self._get_subset_stack()

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
        stack = []
        geo_ref_stack = self.geo_reference.stack(opts=self.opts)

        for i, ref in enumerate(geo_ref_stack):
            for j, sec in enumerate(geo_ref_stack):
                if i < j and not ref.baseline.get("noStateVectors") and not sec.baseline.get("noStateVectors"):
                    pair = Pair(ref, sec)
                    stack.append(pair)
    
        return stack

    def _get_subset_stack(self):
        self.subset_stack = []
        for pair in self.full_stack:
            if (pair.ref_date, pair.sec_date) not in self.date_pair_remove_list:
                self.subset_stack.append(pair)


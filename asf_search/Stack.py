from collections import defaultdict, deque
from copy import copy
from datetime import date
from typing import Optional, List, Tuple, Union
import warnings

from .ASFProduct import ASFProduct
from .Pair import Pair
from .ASFSearchOptions import ASFSearchOptions
from .ASFSearchResults import ASFSearchResults
from .warnings import PairNotInFullStackWarning

try:
    from ciso8601 import parse_datetime
except ImportError:
    from dateutil.parser import parse as parse_datetime

class Stack:
    """
    A Stack object contains 4+ lists of Pair objects. Each Pair contains a pair of asf_search.ASFProduct objects.
    
    Stack member variables holding lists of Pairs:
    - Stack.full_stack: Every possible pair based on the provided geo_reference scene 
      and ASFSearchOptions. This forms a complete network of all represented asf_search.ASFProducts.
    - Stack.remove_list: The list of Pairs to remove from Stack.full_stack, used to create Stack.subset_stack
    - Stack.subset_stack: The resulting list after removing Stack.Remove_list from Stack.full_stack. This creates 
      a possibly disconnected network of asf_search.ASFProducts
    - Stack.connected_substacks: This is a list of lists of Pairs. It contains each disconnected component of a Stack.subset_stack's
      asf_search.ASFProduct network. A length of 1 indicates that Stack.subset_stack is a connected network of asf_search.ASFProducts.

    Public Stack methods:
    - Stack.remove_pairs(): Adds Pairs to Stack.remove_list and removes them from Stack.subset_stack.
    - Stack.add_pairs(): Adds Pairs to Stack.subset_stack. This either removes them from Stack.remove_list, or if not yet present in the
      Stack, adds them to self.full_stack.
    - Stack.get_scene_ids(): A convenience method that returns a given list of Pairs as a list of tuples of asf_search.ASFProduct
      product IDs, which is useful when ordering on-demand processing via ASF's HyP3 or HyP3+ services.
    """


    @property
    def scene_ids(self) -> List[Tuple[str, str]]:
        """
        Provides scene names for all asf_search.ASFProducts in the largest connected substack
        Useful when ordering pair-based products from ASF HyP3 On-Demand Processing.

        Use the get_scene_ids method to get the IDs for other pair lists (full_stack, subset_stack, 
        any network in connected_substacks, or remove_list)
        
        Returns:
            A list tuples containing the reference and secondary scene names for each `Pair` in a `Pair` list
        """
        pair_list = max(self.connected_substacks, key=len)

        return [
            (pair.ref.properties["sceneName"], pair.sec.properties["sceneName"])
            for pair in pair_list
            ]
    

    def __init__(
        self,
        geo_reference: ASFProduct,
        opts: Optional[ASFSearchOptions] = None,
        allow_missing_state_vectors: Optional[bool] = False
    ):
        """
        Constructor that builds a Stack from a geo-reference ASFProduct

        geo_reference: An ASFProduct that serves as a geo-reference scene for the Stack
        opts: (Optional) ASFSearchOptions to apply to the geo_reference.stack() search when creating Stack.full_stack
        """
        self.geo_reference = geo_reference
        if opts is None:
            opts = ASFSearchOptions()
        self.opts = opts
        self.allow_missing_state_vectors = allow_missing_state_vectors
        self.full_stack = self._build_full_stack()
        self._remove_list = []
        self._update_stack()

    @classmethod
    def from_search_results(
        cls,
        stack_search_results: ASFSearchResults,
        allow_missing_state_vectors: Optional[bool] = False
    ):
        """
        Alternate class method constructor using ASFSearchResults instead of a single geo_reference.
        """
        obj = cls.__new__(cls)

        obj.allow_missing_state_vectors = allow_missing_state_vectors
        obj.full_stack = obj._build_full_stack(stack_search_results)
        obj._remove_list = []
        obj.subset_stack = obj._get_subset_stack()
        obj.connected_substacks = obj._find_connected_substacks()
        obj.geo_reference = None

        return obj

    @property
    def remove_list(self) -> List[Pair]:
        """
        Returns a copy of self._remove_list so client changes 
        do not alter self._remove_list without initiating a stack update

        Disallow: 
          - my_stack.remove_list.append(my_pair)
          - my_stack.remove_list.remove(my_pair)

        Support:
          - my_stack.remove_pairs([pair_1, pair_2, ...])
          - my_stack.add_pairs([pair_1, pair_2, ...])
        """
        return copy(self._remove_list)

    @remove_list.setter
    def remove_list(self, pairs: List[Pair]):
        """
        pairs: A list of Pairs to remove from self.subset_stack
        """
        # remove duplicates
        self._remove_list = list(set(pairs))
        self._update_stack()

    def remove_pairs(self, pairs: Union[List[Pair], Pair, Tuple[str], List[Tuple[str]]]):
        """
        Remove pairs from self.subset_stack, 
        i.e., add them to self._remove_list

        Example calls:
            my_stack.remove_pairs(my_pair)
            my_stack.remove_pairs([my_pair_1, my_pair_2, ...])
            my_stack.remove_pairs(("2024-10-20", "2024-11-02"))
            my_stack.remove_pairs([("2024-10-20", "2024-11-02"), ("2024-10-26", "2024-11-02")])

        pairs: A Pair or list of Pairs to remove from self.subset_stack
               or a Tuple of parsable date pair strings
        """
        if not isinstance(pairs, List):
            pairs = [pairs]
        if not isinstance(pairs[0], Pair):
            print(pairs[0][0])
            pairs = [get_pair_from_dates(
                self.subset_stack,
                parse_datetime(date_pair[0]).date(),
                parse_datetime(date_pair[1]).date()) for
                date_pair in pairs]

        for pair in pairs:
            if pair not in self._remove_list:
                if pair in self.full_stack:
                    self._remove_list.append(pair)
                else:
                    msg = f"warning: {pair} is not in full_stack"
                    warnings.warn(PairNotInFullStackWarning(msg))
        self._update_stack()

    def add_pairs(self, pairs: Union[List[Pair], Pair]):
        """
        Add pairs to self.subset_stack and, if necessary, to self.full_stack 
        i.e., remove them from self._remove_list if present or else add them to self.full_stack 

        This allows for the addition of custom pairs that were not originally present
        in self.full_stack

        pairs: A Pair or list of Pairs to add to self.subset_stack
        """
        if isinstance(pairs, Pair):
            pairs = [pairs]

        for pair in pairs:
            if pair in self._remove_list:
                self._remove_list.remove(pair)
            else:
                self.full_stack.append(pair)
        self._update_stack()

    def _build_full_stack(self, stack_search_results: Optional[ASFSearchResults]=None) -> List[Pair]:
        """
        Create self._full_stack, which involves performing a stack search
        of the georeference scene and creating a list of every possible Pair.

        stack_search_results: (Optional) ASFSearchResults from an ASFProduct.stack search
        """
        if stack_search_results is None: 
            stack_search_results = self.geo_reference.stack(opts=self.opts)

        return [
            Pair(p1, p2)
            for i, p1 in enumerate(stack_search_results)
            for p2 in stack_search_results[i + 1:]
            if self.allow_missing_state_vectors or Pair(p1, p2).perpendicular_baseline is not None
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
        These two things should always happen together.
        """
        self.subset_stack = self._get_subset_stack()
        self.connected_substacks = self._find_connected_substacks()

    def _find_connected_substacks(self) -> List[List[Pair]]:
        """
        Perform a bredth first search to find all connected components of self.subset_stack
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
                component_pairs = [v for v in component_pairs.values()]
                components.append(component_pairs)

        return components


    def get_scene_ids(self, pair_list: Optional[List[Pair]] = None) -> List[Tuple[str, str]]:
        """
        Provides scene names for all asf_search.ASFProducts in a list of Pairs.
        Useful when ordering pair-based products from ASF HyP3 On-Demand Processing.

        If no stack_dict is passed, defaults to the largest connected substack

        pair_list: (Optional) A list of `Pair`s for which to retrieve scene IDs.
        
        Returns:
            A list tuples containing the reference and secondary scene names for each `Pair` in a `Pair` list
        """
        if not pair_list:
            return self.scene_ids

        return [
            (pair.ref.properties["sceneName"], pair.sec.properties["sceneName"])
            for pair in pair_list
            ]
    
def get_pair_from_dates(pair_list: List[Pair],
                            ref_date: date, sec_date: date) -> Pair:
    """
    This convenience method allows for the retrieval of a Pair object from a list
    of Pairs by reference and secondary date. This is usefull when identifying a 
    Pair object for removal or addition to an SBASNetwork.subset_stack

    pair_list: a list of Pairs from which to find a Pair object
    ref_date: a datetime.date of a target Pair's reference scene
    sec_date: a datetime.date of a target Pair's secondary scene

    Returns: A Pair with a corresponding ref_date and sec_date
    """
    for pair in pair_list:
        if pair.ref_time.date() == ref_date and pair.sec_time.date() == sec_date:
            return pair
    raise ValueError(f"No Pairs found corresponding to reference date: {ref_date}, secondary date: {sec_date}")
            
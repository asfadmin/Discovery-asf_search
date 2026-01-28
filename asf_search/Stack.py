from collections import defaultdict, deque
from copy import copy
from typing import Optional, List, Tuple
import warnings

from .ASFProduct import ASFProduct
from .Pair import Pair
from .ASFSearchOptions import ASFSearchOptions
from .warnings import PairNotInFullStackWarning

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
    def __init__(
        self,
        geo_reference: ASFProduct,
        opts: Optional[ASFSearchOptions] = None
    ):
        self.geo_reference = geo_reference
        if opts is None:
            opts = ASFSearchOptions()
        self.opts = opts
        self.full_stack = self._build_full_stack()
        self._remove_list = []
        self.subset_stack = self._get_subset_stack()
        self.connected_substacks = self._find_connected_substacks()

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

    def remove_pairs(self, pairs: List[Pair]):
        """
        Remove pairs from self.subset_stack, 
        i.e., add them to self._remove_list

        pairs: A list of Pairs to remove from self.subset_stack
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
        i.e., remove them from self._remove_list if present or else add them to self.full_stack 

        This allows for the addition of custom pairs that were not originally present
        in self.full_stack

        pairs: A list of Pairs to add to self.subset_stack
        """
        for pair in pairs:
            if pair in self._remove_list:
                self._remove_list.remove(pair)
            else:
                self.full_stack.append(pair)
        self._update_stack()

    def _build_full_stack(self) -> List[Pair]:
        """
        Create self._full_stack, which involves performing a stack search
        of the georeference scene and creating a list of every possible Pair.
        """
        geo_ref_stack = self.geo_reference.stack(opts=self.opts)
        return [
            Pair(p1, p2)
            for i, p1 in enumerate(geo_ref_stack)
            for p2 in geo_ref_stack[i+1:]
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

                components.append(component_pairs)

        return components

    def get_scene_ids(self, pair_list: Optional[List[Pair]] = None) -> List[Tuple[str, str]]:
        """
        Provides scene names for all asf_search.ASFProducts in a list of Pairs.
        Useful when ordering pair-based products from ASF HyP3 On-Demand Processing.

        If no stack_dict is passed, defaults to the largest connected substack

        pair_list: A list of `Pair`s for which to retrieve scene IDs.
        
        Returns:
            A list tuples containing the reference and secondary scene names for each `Pair` in a `Pair` list
        """
        if not pair_list:
            pair_list = max(self.connected_substacks, key=len)

        return [
            (pair.ref.properties["sceneName"], pair.sec.properties["sceneName"])
            for pair in pair_list
            ]
    
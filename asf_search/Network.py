from collections import Counter
from datetime import datetime, date, timedelta
import importlib.util
import numpy as np
import pandas as pd
from typing import Optional, Dict, Tuple, List
import warnings

from .ASFProduct import ASFProduct
from .Pair import Pair
from .Stack import Stack
from .MultiBurst import MultiBurst
from .search import geo_search
from .ASFSearchOptions import ASFSearchOptions
from .constants import PLATFORM
from .warnings import OptionalDependencyWarning
from asf_search import ASF_LOGGER


class Network(Stack):
    """
    Network is a child class of Stack, used to create seasonal SBAS stacks. It can be used
    to create multiannual stacks connected with multiannual bridge pairs.
    """
    def __init__(
        self,
        geo_reference: Optional[ASFProduct] = None,
        multiburst: Optional[MultiBurst] = None,
        perp_baseline: Optional[int] = 400,
        inseason_temporal_baseline: Optional[int] = 36,
        bridge_year_threshold: Optional[int] = 1,
        bridge_target_date: Optional[str] = None,
        opts: Optional[ASFSearchOptions] = None
    ):
        """
        geo_reference: an ASFProduct used as a georeference scene for the stack
        multiburst: a MultiBurst object describing a collection of bursts for a multi-burst Network
        
        (pass geo_reference xor multiburst)

        perp_baseline: the perpendicular baseline for the SBAS stack
        inseason_temporal_baseline: the temporal baseline for the SBAS stack, not accounting for multiannual bridging
        bridge_year_threshold: the number of year for which to allow multiannual bridging
        bridge_target_date: %m-%d string of the inseason bridge date to target. 
                            Reference scenes for bridge pairs are valid within an inseason_temporal_baseline of this date.
        opts: ASFSearchOptions to limit the size of your Network and define seasons
              Recommended to include: "start", "end", "season"
        """
        xor_err_str = "geo_reference or multiburst must be passed, but not both"
        assert (geo_reference is None) ^ (multiburst is None), xor_err_str

        self._season = opts.season if opts.season is not None else (1, 365)
        if bridge_target_date:
            self.bridge_target_date = bridge_target_date
        else:
            self.bridge_target_date = self._season[0]
        self._start = getattr(opts, "start", None)
        self._end = getattr(opts, "end", None)
        self.perp_baseline = perp_baseline
        self.inseason_temporal_baseline = inseason_temporal_baseline
        self.bridge_year_threshold = bridge_year_threshold
        self.opts = opts

        self.additional_multiburst_networks = []
        if geo_reference is None:
            self.multiburst = multiburst
            geo_reference, self.additional_multiburst_networks = self._get_georef_and_multiburst_networks()

        self.temporal_baseline = (bridge_year_threshold * 365) + inseason_temporal_baseline

        super().__init__(
            geo_reference=geo_reference, 
            temporal_baseline=self.temporal_baseline, 
            opts=self.opts
            )

        self._build_sbas_stack()
        if self.additional_multiburst_networks:
            self._interesect_multiburst_stacks()

        # warn user if they lack optional dependencies for plotting
        missing_optional_deps = []
        if importlib.util.find_spec("plotly") is None:
            missing_optional_deps.append("plotly")
        if importlib.util.find_spec("networkx") is None:
            missing_optional_deps.append("networkx")
        if missing_optional_deps:
            msg = (
                "Warning: Network.plot() requires the dependencies plotly and networkx."
                f"You are currently missing: {missing_optional_deps}."
                "However, your Network is still available without access to plotting."
            )
            warnings.warn(OptionalDependencyWarning(msg))

    def _get_georef_and_multiburst_networks(self):
        """
        Identify geo-reference bursts for all multi-burst stacks. Return the first burst stack's geo-reference burst ID and a list
        of Networks created from each remaining geo-reference burst ID
        """
        flight_direction = self.multiburst.burst_metadata[0]['items'][0]['umm']['AdditionalAttributes'][0]['Values'][0]
        next_year = pd.to_datetime(self._start) + pd.DateOffset(years=1)
        geo_search_opts = {
            'platform': PLATFORM.SENTINEL1,
            'season': self._season,
            'start': self._start,
            'end': next_year,
            'polarization': 'VV',
            'processingLevel': 'BURST',
            'flightDirection': flight_direction,
            'intersectsWith': self.multiburst.extent_wkt,
        }
        results = geo_search(**geo_search_opts)
        if len(results) == 0:
            raise Exception("Found no geo-reference scenes within one year of start date ({self._start})")

        additional_multiburst_networks = []
        burst_stacks = []

        for i, burst_id in enumerate(self.multiburst.burst_ids):
            burst_stack = [burst for burst in results if burst_id[4:] in burst.properties['sceneName']]
            burst_stacks.append(burst_stack)

            if i == 0:
                geo_reference = burst_stack[-1]
            else:
                multiburst_network = Network(
                    geo_reference=results[-1],
                    perp_baseline=self.perp_baseline, 
                    inseason_temporal_baseline=self.inseason_temporal_baseline,
                    bridge_target_date=self.bridge_target_date,
                    bridge_year_threshold=self.bridge_year_threshold,
                    opts=self.opts)
                additional_multiburst_networks.append(multiburst_network)
        return geo_reference, additional_multiburst_networks

    def _interesect_multiburst_stacks(self):
        """
        This function validates multiburst sbas stacks.
        It is possible that not all burst stacks will contain the same set of date pairs. 
        A valid multiburst SBAS stack should contain complete coverage over every burst, in
        every date pair. 
        
        Any burst pair that is not present in every burst stack is removed from all stacks.
        """
        all_subset_stacks = [i.subset_stack for i in self.additional_multiburst_networks]
        all_subset_stacks.append(self.subset_stack)
        all_subset_pairs = [kv[0] for subset_stack in all_subset_stacks for kv in subset_stack.items()]
        all_subset_pairs_count = Counter(all_subset_pairs)
        underrepresented_pairs = [pair for pair in all_subset_pairs_count
                                  if all_subset_pairs_count[pair] < len(self.additional_multiburst_networks) + 1]

        all_networks = [network for network in self.additional_multiburst_networks]
        all_networks.append(self)
        for pair in underrepresented_pairs:
            for network in all_networks:
                if pair in network.subset_stack:
                    ASF_LOGGER.info(f"Removing pair not present in all multiburst stacks: {pair}")
                    network.remove_pairs([pair])

    def _passes_temporal_check(self, pair: Pair):
        """
        Logic to determine if a pair should be included in subset_stack
        based on temporal baselines. It takes into account possible
        multiannual bridge pairs to create seasonal, mutliannual SBAS stacks

        pair: the Pair to check
        """
        # return True right away if pair within inseason temp baseline
        if pair.temporal.days <= self.inseason_temporal_baseline:
            return True

        # determine season length, accounting for seasons that span years (e.g. Nov-May)
        if self._season[0] < self._season[1]:
            season_length = self._season[1] - self._season[0] + 1
        else:
            season_length = 366 - self._season[0] + self._season[1]

        # Only create multiannual bridge pairs if the off-season is longer than inseason_temporal_baseline
        if 365 - season_length > self.inseason_temporal_baseline:

            # determine how far ref scene date is from target multi-annual bridge date 
            days_from_bridge_date = np.abs(
                (
                    datetime.strptime(f"{self.bridge_target_date}-{pair.ref_date.year}", "%m-%d-%Y").date() 
                    - pair.ref_date).days
                )
            # Create lists of valid secondary scene date ranges.
            # The number of years bridged is determined by the bridge_year_threshold.
            valid_ranges = []
            for i in range(1, self.bridge_year_threshold+1):
                valid_ranges.append((i * 365 - self.inseason_temporal_baseline, i * 365 + self.inseason_temporal_baseline))

            # return True if the ref scene is within the inseason_temporal_baseline of
            # the target bridge date and the secondary scene falls within a valid date range
            return days_from_bridge_date <= self.inseason_temporal_baseline and \
                any(start <= pair.temporal.days <= end for start, end in valid_ranges)
        else:
            return False

    def _build_sbas_stack(self):
        """
        Create a self.remove_list that subset full_stack to the SBAS stack/s
        """
        remove_list = []
        for pair in self.full_stack.values():
            if np.abs(pair.perpendicular) > self.perp_baseline or not \
                self._passes_temporal_check(pair):
                remove_list.append((pair.ref_date, pair.sec_date))
        self.remove_list = remove_list

    def plot(self, stack_dict: Dict[Tuple[date, date], Pair] = None):
        """
        Plot the SBAS stack(s). Accepts a stack_dict or a list of stack_dicts.
        The largest stack is plotted in blue; others are plotted in distinct colors.
        Possible member stacks to pass as stack_dict are: 
            - `self.full_stack`: includes every possible pair in the stack, ignoring baselines
            - `self.subset_stack`: a possibly disconnected SBAS stack
            - `self.connected_substacks`: subset_stack, broken up into connected substacks

        stack_dict (optional): One of the Network's stacks (options listed above).
                               Default: `self.connected_substacks`.
        """
        import plotly.graph_objects as go
        import networkx as nx
        from plotly.colors import sample_colorscale

        def get_n_colors(n, colorscale="Rainbow", alpha=0.4):
            base_colors = sample_colorscale(colorscale, [i / max(n - 1, 1) for i in range(n)])
            rgba_colors = []
            for color_str in base_colors:
                if color_str.startswith("rgb"):
                    nums = color_str.strip("rgb()").split(",")
                    r, g, b = [int(x) for x in nums]
                    rgba_colors.append(f"rgba({r}, {g}, {b}, {alpha})")
                else:
                    raise ValueError(f"Unexpected color format: {color_str}")
            return rgba_colors

        if not stack_dict:
            stack_dicts = self.connected_substacks
        elif isinstance(stack_dict, list):
            stack_dicts = stack_dict
        else:
            stack_dicts = [stack_dict]

        # Identify the largest stack
        largest_stack = max(stack_dicts, key=lambda s: len(s))
        other_stacks = [s for s in stack_dicts if s is not largest_stack]

        # Create a graph including all pairs from all stacks
        node_products = {}
        for stack in stack_dicts:
            for pair in stack.values():
                for date_obj, product in [(pair.ref_date, pair.ref), (pair.sec_date, pair.sec)]:
                    date_str = datetime.strftime(date_obj, "%Y-%m-%d")
                    if date_str not in node_products:
                        node_products[date_str] = product

        G = nx.DiGraph()
        for date_str, product in node_products.items():
            G.add_node(date_str)
            G.nodes[date_str]["date"] = date_str
            G.nodes[date_str]["perp_bs"] = Pair(self.geo_reference, product).perpendicular

        node_positions = {
            node: datetime.strptime(data["date"], "%Y-%m-%d").timestamp()
            for node, data in G.nodes(data=True)
        }
        node_y_positions = {
            node: data["perp_bs"] for node, data in G.nodes(data=True)
        }

        # Add blue edges for the largest stack
        insar_node_pairs = [
            (
                datetime.strftime(pair.ref_date, "%Y-%m-%d"),
                datetime.strftime(pair.sec_date, "%Y-%m-%d"),
                {
                    "perp_bs": pair.perpendicular,
                    "temp_bs": pair.temporal.days
                }
            )
            for pair in largest_stack.values()
        ]
        G.add_edges_from(insar_node_pairs, data=True)

        edge_x = []
        edge_y = []
        edge_text = []
        for edge in G.edges(data=True):
            x0 = node_positions[edge[0]]
            y0 = node_y_positions[edge[0]]
            x1 = node_positions[edge[1]]
            y1 = node_y_positions[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_text.append(
                f"{edge[0]} - {edge[1]}, perp baseline: {edge[2]['perp_bs']}, temp baseline: {edge[2]['temp_bs']}"
            )

        edge_traces = [
            go.Scatter(
                x=edge_x,
                y=edge_y,
                line=dict(width=4, color="rgba(52, 114, 168, 0.7)"),  # blue
                mode="lines",
            ),
            go.Scatter(
                x=[
                    (node_positions[edge[0]] + node_positions[edge[1]]) / 2
                    for edge in G.edges()
                ],
                y=[
                    (node_y_positions[edge[0]] + node_y_positions[edge[1]]) / 2
                    for edge in G.edges()
                ],
                mode="markers",
                marker=dict(size=20, color="rgba(255, 255, 255, 0)"),
                hoverinfo="text",
                text=edge_text,
            )
        ]

        # Add additional substacks
        colors = get_n_colors(len(other_stacks))
        for color, other_stack in zip(colors, other_stacks):
            edge_x = []
            edge_y = []
            for pair in other_stack.values():
                ref = datetime.strftime(pair.ref_date, "%Y-%m-%d")
                sec = datetime.strftime(pair.sec_date, "%Y-%m-%d")
                if ref in node_positions and sec in node_positions:
                    edge_x.extend([node_positions[ref], node_positions[sec], None])
                    edge_y.extend([node_y_positions[ref], node_y_positions[sec], None])
            edge_traces.append(go.Scatter(
                x=edge_x,
                y=edge_y,
                line=dict(width=4, color=color),
                mode="lines",
            ))

            edge_text = []
            hover_x = []
            hover_y = []
            for pair in other_stack.values():
                ref = datetime.strftime(pair.ref_date, "%Y-%m-%d")
                sec = datetime.strftime(pair.sec_date, "%Y-%m-%d")
                if ref in node_positions and sec in node_positions:
                    edge_text.append(
                        f"{ref} - {sec}, perp baseline: {pair.perpendicular}, temp baseline: {pair.temporal.days}"
                    )
                    hover_x.append((node_positions[ref] + node_positions[sec]) / 2)
                    hover_y.append((node_y_positions[ref] + node_y_positions[sec]) / 2)

            edge_traces.append(go.Scatter(
                x=hover_x,
                y=hover_y,
                mode="markers",
                marker=dict(size=20, color="rgba(255, 255, 255, 0)"),
                hoverinfo="text",
                text=edge_text,
            ))

        # Add used scene nodes
        node_x = [node_positions[node] for node in G.nodes()]
        node_y = [node_y_positions[node] for node in G.nodes()]
        node_text = [G.nodes[node]["date"] for node in G.nodes()]

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            textposition="top center",
            marker=dict(size=15, color="rgba(32, 33, 32, 0.7)", line_width=0),
            hoverinfo="text",
            hovertext=node_text,
        )

        # Add unused scene nodes
        all_slcs = set(scene for pair in self.full_stack.values() for scene in (pair.ref, pair.sec))
        used_slcs = set()
        for sd in stack_dicts:
            used_slcs.update(scene for pair in sd.values() for scene in (pair.ref, pair.sec))
        unused_slcs = list(all_slcs - used_slcs)

        unused_slc_dates_str = [i.properties["stopTime"].split("T")[0] for i in unused_slcs]
        unused_slc_dates_x = [datetime.strptime(i, "%Y-%m-%d").timestamp() for i in unused_slc_dates_str]
        unused_slc_perp_y = [Pair(self.geo_reference, i).perpendicular for i in unused_slcs]

        unused_slcs_trace = go.Scatter(
            x=unused_slc_dates_x, y=unused_slc_perp_y,
            mode='markers',
            hoverinfo='text',
            text=unused_slc_dates_str,
            marker=dict(
                color='rgba(255,0,0,0.5)',
                size=10,
                line_width=2
            )
        )

        # Define the date (x) axis
        date_range = (
            pd.date_range(
                start="-".join(self.opts.start.split("-")[:2]),
                end="-".join(self.opts.end.split("-")[:2]),
                freq="MS"
            )
            .strftime("%Y-%m")
            .tolist()
        )
        date_range_ts = [datetime.strptime(date, "%Y-%m").timestamp() for date in date_range]

        def julian_to_month_day(julian_tuple):
            year = int(self.geo_reference.properties['stopTime'].split('-')[0])
            month_day = []
            for day in julian_tuple:
                date = datetime(year, 1, 1) + timedelta(days=day - 1)
                month_day.append(date.strftime("%m-%d"))
            return tuple(month_day)

        largest_stack_slc_count = len(set(scene for pair in largest_stack.values() for scene in (pair.ref, pair.sec)))

        if stack_dict is self.full_stack:
            plot_header_text = (
                "<b>SBAS Stack</b><br>"
                f"Geographic Reference: {self.geo_reference.properties["sceneName"]}<br>"
                f"Temporal Bounds: {self._start.split('T')[0]} - {self._end.split('T')[0]}, "
                f"Seasonal Bounds: {julian_to_month_day(self._season)}<br>"
                f"Full Stack Size: {len(largest_stack)} pairs from {largest_stack_slc_count} scenes<br>"
            )
        else:
            plot_header_text = (
                "<b>SBAS Stack</b><br>"
                f"Geographic Reference: {self.geo_reference.properties["sceneName"]}<br>"
                f"Temporal Bounds: {self._start.split('T')[0]} - {self._end.split('T')[0]}, "
                f"Seasonal Bounds: {julian_to_month_day(self._season)}<br>"
                f"Temporal Baseline: {self.inseason_temporal_baseline} days, "
                f"Perpendicular Baseline: {self.perp_baseline}m<br>"
                f"Bridge Target Date: {self.bridge_target_date}, Largest Stack Size: "
                f"{len(largest_stack)} pairs from {largest_stack_slc_count} scenes<br>"
            )

        fig = go.Figure(
            data=edge_traces + [node_trace, unused_slcs_trace],
            layout=go.Layout(
                showlegend=False,
                hovermode="closest",
                height=800,
                margin=dict(t=180),
                xaxis=dict(
                    title="Acquisition Date",
                    tickvals=date_range_ts,
                    ticktext=date_range,
                    gridcolor="gray",
                    zerolinecolor="gray",
                ),
                yaxis=dict(
                    title="Perpendicular Baseline (m)",
                    gridcolor="gray",
                    zerolinecolor="gray",
                ),
                title=dict(
                    text=plot_header_text,
                    y=0.95,
                    x=0.5,
                    xanchor="center",
                    yanchor="top",
                    font=dict(family="Helvetica, monospace", size=22),
                ),
                plot_bgcolor="white",
                paper_bgcolor="lightgrey",
            ),
        )
        fig.show()

    def get_multi_burst_pair_ids(self, stack_dict_name: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        Useful when ordering a multi-burst SBAS stack from ASF HyP3 On-Demand Processing.
        Provides InSAR pairs in cooresponding lists of reference and secondary scene IDs

        If no stack_dict is passed, defaults to using the largest connected substack
        Appends cooresponding stack_dicts from each additional multi-burst network

        Returns:
            a list of reference scene IDs and a matching list of secondary scene names for every
            inSAR pair in the multi- burst SBAS stack
        """
        if not stack_dict_name:
            stack_dict = max(self.connected_substacks, key=len)
            stack_dicts = [max(d.connected_substacks, key=len) for d in self.additional_multiburst_networks]
        else:
            stack_dict = getattr(self, stack_dict_name)
            stack_dicts = [getattr(d, stack_dict_name) for d in self.additional_multiburst_networks]

        stack_dicts.append(stack_dict)
        ref_scenes = [v.ref.properties['sceneName'] for d in stack_dicts for (k, v) in d.items()]
        sec_scenes = [v.sec.properties['sceneName'] for d in stack_dicts for (k, v) in d.items()]
        return ref_scenes, sec_scenes

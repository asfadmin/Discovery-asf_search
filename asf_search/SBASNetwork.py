from datetime import datetime, timedelta
import importlib.util
import numpy as np
import pandas as pd
from typing import Optional, List
import warnings

from .ASFProduct import ASFProduct
from .Pair import Pair
from .Stack import Stack
from .ASFSearchOptions import ASFSearchOptions
from .warnings import OptionalDependencyWarning
from .ASFSearchResults import ASFSearchResults

class SBASNetwork(Stack):
    """
    SBASNetwork is a child class of Stack, used to create seasonal SBAS networks. It can be used
    to create multiannual networks connected with multiannual bridge pairs.
    """
    def __init__(
        self,
        geo_reference: Optional[ASFProduct] = None,
        perpendicular_baseline: Optional[int] = 400,
        inseason_temporal_baseline: Optional[int] = 36,
        bridge_year_threshold: Optional[int] = 1,
        bridge_target_date: Optional[str] = None,
        opts: Optional[ASFSearchOptions] = None
    ):
        """
        geo_reference: an ASFProduct used as a georeference scene for the network
        multiburst: a MultiBurst object describing a collection of bursts for a multi-burst SBASNetwork
        
        (pass geo_reference xor multiburst)

        perpendicular_baseline: the perpendicular baseline for the SBAS network
        inseason_temporal_baseline: the temporal baseline for the SBAS network, not accounting for multiannual bridging
        bridge_year_threshold: the number of year for which to allow multiannual bridging
        bridge_target_date: %m-%d string of the inseason bridge date to target. 
                            Reference scenes for bridge pairs are valid within an inseason_temporal_baseline of this date.
        opts: ASFSearchOptions to limit the size of your SBASNetwork and define seasons
              Recommended to include: "start", "end", "season"
        """
        self._season = opts.season if opts.season is not None else (1, 365)
        if bridge_target_date:
            self.bridge_target_date = bridge_target_date
        else:
            self.bridge_target_date = self._season[0]
        self._start = getattr(opts, "start", None)
        self._end = getattr(opts, "end", None)
        self.perpendicular_baseline = perpendicular_baseline
        self.inseason_temporal_baseline = inseason_temporal_baseline
        self.bridge_year_threshold = bridge_year_threshold
        self.opts = opts

        self.temporal_baseline = (bridge_year_threshold * 365) + inseason_temporal_baseline

        super().__init__(
            geo_reference=geo_reference, 
            opts=self.opts
            )

        self._build_sbas_network()

        # warn user if they lack optional dependencies for plotting
        missing_optional_deps = []
        if importlib.util.find_spec("plotly") is None:
            missing_optional_deps.append("plotly")
        if importlib.util.find_spec("networkx") is None:
            missing_optional_deps.append("networkx")
        if missing_optional_deps:
            msg = (
                "Warning: SBASNetwork.plot() requires the dependencies plotly and networkx."
                f"You are currently missing: {missing_optional_deps}."
                "However, your SBASNetwork is still available without access to plotting."
            )
            warnings.warn(OptionalDependencyWarning(msg))

    def _build_full_stack(self, stack_search_results: Optional[ASFSearchResults]=None) -> List[Pair]:
        """
        Create self._full_stack, which involves performing a stack search
        of the georeference scene and creating a list of every possible Pair.

        Overrides Stack._build_full_stack() to naively exclude pairs based on self.perpendicular_baseline,
        self.inseason_temporal_baseline, and self.bridge_year_threshold. This is done for efficiency, to
        avoid build massive full_stacks. More targeted occures in self._build_sbas_network()

        stack_search_results: (Optional) ASFSearchResults from an ASFProduct.stack search

        Returns: A list of pairs filtered by baselines, and including every possible bridge pair within 
                 self.bridge_year_threshold
        """
        if stack_search_results is None: 
            stack_search_results = self.geo_reference.stack(opts=self.opts)

        return [
            Pair(p1, p2)
            for i, p1 in enumerate(stack_search_results)
            for p2 in stack_search_results[i+1:]
            if Pair(p1, p2).perpendicular_baseline <= self.perpendicular_baseline
            and Pair(p1, p2).temporal_baseline.days <= self.inseason_temporal_baseline + (self.bridge_year_threshold * 365)
        ]

    def _is_valid_bridge_pair(self, pair: Pair) -> bool:
        """
        Logic to determine if a pair meets the criteria for including in an SBAS network as a bridge pair:
        - reference scene date within 1/2 self.inseason_temporal_baseline on either side of self.bridge_target_date
        - secondary scene within 1/2 self.inseason_temporal_baseline on either side of self.bridge_target_date for 
          each year within the self.bridge_year_threshold

        pair: the Pair to check
        """
        # return True right away if pair within inseason temp baseline
        if pair.temporal_baseline.days <= self.inseason_temporal_baseline:
            return True

        # determine how far ref scene date is from target multi-annual bridge date 
        days_from_bridge_date = np.abs(
            (
                datetime.strptime(f"{self.bridge_target_date}-{pair.ref_time.year}", "%m-%d-%Y") 
                - pair.ref_time.replace(tzinfo=None)).days
            )
        
        half_inseason_temporal_baseline = self.inseason_temporal_baseline / 2

        # Create lists of valid secondary scene date ranges.
        # The number of years bridged is determined by the bridge_year_threshold.
        valid_ranges = []
        for i in range(1, self.bridge_year_threshold+1):
            valid_ranges.append((i * 365 - half_inseason_temporal_baseline, i * 365 + half_inseason_temporal_baseline))

        # return True if the ref scene is within the inseason_temporal_baseline / 2 on either
        # side of the target bridge date and the secondary scene falls within a valid date range
        return days_from_bridge_date <= half_inseason_temporal_baseline and \
            any(start <= pair.temporal_baseline.days <= end for start, end in valid_ranges)

    def _build_sbas_network(self):
        """
        Create a self._remove_list for filtering self.full_stack to produce self.subset_stack.
        Initial temporal and perpendicular baselng occur in SBASNetwork._build_full_stack().
        This method appies additional filtering to remove potential pairs based on self.inseason_temporal_baseline
        and self.bridge_year_threshold
        """
        remove_list = []
        for pair in self.full_stack:
            if not self._is_valid_bridge_pair(pair):
                remove_list.append(pair)
        self.remove_list = remove_list

    def plot(self, pair_list: List[Pair] = None):
        """
        Plot the SBAS network(s). Accepts a pair_list or a list of pair_lists.
        The largest network is plotted in blue; others are plotted in distinct colors.
        Possible member networks to pass as pair_list are: 
            - `self.full_stack`: an SBAS network filtered by baselines, and including every possible bridge pair within 
               self.bridge_year_threshold
            - `self.subset_stack`: a possibly disconnected SBAS network filtered by baselines, with additional 
               bridge pair filtering applied
            - `self.connected_substacks`: self.subset_stack, broken up into a list of connected sub-networks

        pair_list (optional): One of the SBASNetwork's pair lists or lists of pair list (options listed above).
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

        if not pair_list:
            pair_lists = self.connected_substacks
        else:
            pair_lists = [pair_list]

        # Identify the largest network
        largest_network = max(pair_lists, key=lambda s: len(s))
        other_networks = [s for s in pair_lists if s is not largest_network]

        # Create a graph including all pairs from all networks
        node_products = {}
        for network in pair_lists:
            for pair in network:
                for date_obj, product in [(pair.ref_time, pair.ref), (pair.sec_time, pair.sec)]:
                    date_str = datetime.strftime(date_obj, "%Y-%m-%d")
                    if date_str not in node_products:
                        node_products[date_str] = product

        G = nx.DiGraph()
        for date_str, product in node_products.items():
            G.add_node(date_str)
            G.nodes[date_str]["date"] = date_str
            G.nodes[date_str]["perp_bs"] = Pair(self.geo_reference, product).perpendicular_baseline

        node_positions = {
            node: datetime.strptime(data["date"], "%Y-%m-%d").timestamp()
            for node, data in G.nodes(data=True)
        }
        node_y_positions = {
            node: (data["perp_bs"] if data.get("perp_bs") else 0)
            for node, data in G.nodes(data=True)
        }

        # Add blue edges for the largest network
        insar_node_pairs = [
            (
                datetime.strftime(pair.ref_time, "%Y-%m-%d"),
                datetime.strftime(pair.sec_time, "%Y-%m-%d"),
                {
                    "perp_bs": pair.perpendicular_baseline,
                    "temp_bs": pair.temporal_baseline.days
                }
            )
            for pair in largest_network
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

        # Add additional sub-networks
        colors = get_n_colors(len(other_networks))
        for color, other_network in zip(colors, other_networks):
            edge_x = []
            edge_y = []
            for pair in other_network:
                ref = datetime.strftime(pair.ref_time, "%Y-%m-%d")
                sec = datetime.strftime(pair.sec_time, "%Y-%m-%d")
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
            for pair in other_network:
                ref = datetime.strftime(pair.ref_time, "%Y-%m-%d")
                sec = datetime.strftime(pair.sec_time, "%Y-%m-%d")
                if ref in node_positions and sec in node_positions:
                    edge_text.append(
                        f"{ref} - {sec}, perp baseline: {pair.perpendicular_baseline}, temp baseline: {pair.temporal_baseline.days}"
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
        all_slcs = set(scene for pair in self.full_stack for scene in (pair.ref, pair.sec))
        used_slcs = set()
        for sd in pair_lists:
            used_slcs.update(scene for pair in sd for scene in (pair.ref, pair.sec))
        unused_slcs = list(all_slcs - used_slcs)

        unused_slc_dates_str = [i.properties["stopTime"].split("T")[0] for i in unused_slcs]
        unused_slc_dates_x = [datetime.strptime(i, "%Y-%m-%d").timestamp() for i in unused_slc_dates_str]
        unused_slc_perp_y = [Pair(self.geo_reference, i).perpendicular_baseline for i in unused_slcs]

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

        def get_pair_lists_date_range(pair_lists):
            start_dates, end_dates = [], []
            for pair_list in pair_lists:
                start_dates.append(min([pair.ref_time for pair in pair_list]))
                end_dates.append(max([pair.sec_time for pair in pair_list]))

            start_date = min(start_dates)
            start_date_str = f"{start_date.year}-{start_date.month}"
            end_date = max(end_dates)
            end_date_str = f"{end_date.year}-{end_date.month}"

            return start_date_str, end_date_str
        
        start_date, end_date = get_pair_lists_date_range(pair_lists)
        date_range = (
            pd.date_range(
                start=start_date,
                end=end_date,
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

        largest_network_slc_count = len(set(scene for pair in largest_network for scene in (pair.ref, pair.sec)))

        if pair_list is self.full_stack:
            plot_header_text = (
                "<b>SBAS Stack</b><br>"
                f"Geographic Reference: {self.geo_reference.properties["sceneName"]}<br>"
                f"Temporal Bounds: {self._start.split('T')[0]} - {self._end.split('T')[0]}, "
                f"Seasonal Bounds: {julian_to_month_day(self._season)}<br>"
                f"Full Stack Size: {len(largest_network)} pairs from {largest_network_slc_count} scenes<br>"
            )
        else:
            plot_header_text = (
                "<b>SBAS Stack</b><br>"
                f"Geographic Reference: {self.geo_reference.properties["sceneName"]}<br>"
                f"Temporal Bounds: {self._start.split('T')[0]} - {self._end.split('T')[0]}, "
                f"Seasonal Bounds: {julian_to_month_day(self._season)}<br>"
                f"Temporal Baseline: {self.inseason_temporal_baseline} days, "
                f"Perpendicular Baseline: {self.perpendicular_baseline}m<br>"
                f"Bridge Target Date: {self.bridge_target_date}, "
                f"Bridge Year Threshold: {self.bridge_year_threshold}, Largest Stack Size: "
                f"{len(largest_network)} pairs from {largest_network_slc_count} scenes<br>"
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

    def get_pair_from_dates(self, pair_list: List[Pair],
                             ref_date: datetime.date, sec_date: datetime.date) -> Pair:
        """
        This convenience method allows for the retrieval of a Pair object from a list
        of Pairs by reference and secondary date. This is usefull when identifying a 
        Pair object for removal or addition to an SBASNetwork.subset_stack

        This method is included in SBASNetwork and not Stack because we only care about
        dates in SBASNetwork and Stack is aware of datetimes.

        pair_list: a list of Pairs from which to find a Pair object
        ref_date: a datetime.date of a target Pair's reference scene
        sec_date: a datetime.date of a target Pair's secondary scene

        Returns: A Pair with a corresponding ref_date and sec_date
        """
        for pair in pair_list:
            if pair.ref_time.date() == ref_date and pair.sec_time.date() == sec_date:
                return pair

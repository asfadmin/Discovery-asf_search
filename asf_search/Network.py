from datetime import datetime
import numpy as np
import pandas as pd

from asf_search import Pair, Stack 
from asf_search.ASFSearchOptions import ASFSearchOptions


class Network(Stack):
    def __init__(self, geo_reference, perp_baseline=400, temporal_baseline=36, bridge_target_date=None, opts=ASFSearchOptions(**{})):
        super().__init__(geo_reference, opts)
        self._season = getattr(opts, "season", ("1-1", "12-31"))
        self._start = getattr(opts, "start", None)
        self._end = getattr(opts, "end", None)

        self.bridge_target_date = bridge_target_date
        self.perp_baseline = perp_baseline
        self.temporal_baseline = temporal_baseline
        # self.overlap_threshold = getattr(opts, "overlapThreshold", 0.8)
        self.network = self._build_sbas_stack()

    def _passes_temporal_check(self, pair):
        if pair.temporal.days <= self.temporal_baseline:
            return True

        days_from_bridge_date = np.abs(
            (datetime.strptime(f"{self.bridge_target_date}-{pair.ref_date.year}", "%m-%d-%Y").date() - pair.ref_date).days
            )
        return days_from_bridge_date <= self.temporal_baseline and \
            365 - self.temporal_baseline <= pair.temporal.days <= 365 + self.temporal_baseline

    def _build_sbas_stack(self):
        remove_list = []
        for pair in self.full_stack.values():
            if np.abs(pair.perpendicular) > self.perp_baseline or not \
                self._passes_temporal_check(pair):
                remove_list.append((pair.ref_date, pair.sec_date))
        self.remove_list = remove_list
        self.subset_stack = self._get_subset_stack()

    def plot(self, stack_dict=None):
        """
        Plot the SBAS stack

        """
        import plotly.graph_objects as go
        import networkx as nx

        if not stack_dict:
            stack_dict = self.subset_stack

        G = nx.DiGraph()

        insar_node_pairs = [
            (
                datetime.strftime(pair.ref_date, "%Y-%m-%d"),
                datetime.strftime(pair.sec_date, "%Y-%m-%d"),
                {
                    "perp_bs": pair.perpendicular,
                    "temp_bs": pair.temporal.days
                }
            )
            for pair in stack_dict.values()]

        G.add_edges_from(insar_node_pairs, data=True)

        scene_date_dict = {
            node: node
            for pair in insar_node_pairs
            for node in (pair[0], pair[1])
        }
        nx.set_node_attributes(G, scene_date_dict, "date")

        perp_bs_dict = {}

        for pair in stack_dict.values():
            for date_obj, product in [
                (pair.ref_date, pair.ref),
                (pair.sec_date, pair.sec)
            ]:
                date_str = datetime.strftime(date_obj, "%Y-%m-%d")
                if date_str not in perp_bs_dict:
                    perp_bs_dict[date_str] = Pair(self.geo_reference, product).perpendicular
        nx.set_node_attributes(G, perp_bs_dict, "perp_bs")

        node_positions = {
            node: datetime.strptime(data["date"], "%Y-%m-%d").timestamp()
            for node, data in G.nodes(data=True)
        }

        node_y_positions = {node: data["perp_bs"] for node, data in G.nodes(data=True)}

        node_x = [node_positions[node] for node in G.nodes()]
        node_y = [node_y_positions[node] for node in G.nodes()]
        node_text = [G.nodes[node]["date"] for node in G.nodes()]

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

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=4, color="rgba(52, 114, 168, 0.7)"),
            mode="lines",
        )

        edge_hover_trace = go.Scatter(
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

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            textposition="top center",
            marker=dict(size=15, color="rgba(32, 33, 32, 0.7)", line_width=0),
            hoverinfo="text",
            hovertext=node_text,
        )

        all_slcs = list(set([scene for pair in self.full_stack.values() for scene in (pair.ref, pair.sec)]))
        used_slcs = list(set([scene for pair in stack_dict.values() for scene in (pair.ref, pair.sec)]))
        unused_slcs = [i for i in all_slcs if i not in used_slcs]
        unused_slc_dates_str = [
            i.properties["processingDate"].split("T")[0]
            for i in unused_slcs
            ]
        unused_slc_dates_x = [
            datetime.strptime(i, "%Y-%m-%d").timestamp()
            for i in unused_slc_dates_str
            ]

        unused_slc_perp_y = [Pair(self.geo_reference, i).perpendicular for i in unused_slcs] #perp baseline to geo ref scene

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

        date_range = (
            pd.date_range(
                start="-".join(self.opts.start.split("-")[:2]), 
                end="-".join(self.opts.end.split("-")[:2]), 
                freq="MS"
            )
            .strftime("%Y-%m")
            .tolist()
        )
        
        date_range_ts = [
            datetime.strptime(date, "%Y-%m").timestamp() for date in date_range
        ]

        # all_y_vals = [pair.perpendicular for ]
        # y_min = min(all_y_vals)
        # y_max = max(all_y_vals)
                
        def f_date(dash_date_str):
            return dash_date_str.replace("-", "/")
        fig = go.Figure(
            data=[edge_trace, edge_hover_trace, node_trace, unused_slcs_trace],
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
                    # range=[y_min-50, y_max+50],
                ),
                title=dict(
                    text=(
                        "<b>Sentinel-1 Seasonal SBAS Stack</b><br>"),
                    #     f"Reference: {self._geo_ref_scene_id}<br>"
                    #     f"Temporal Bounds: {f_date(self._start)} - {f_date(self._end)}, Seasonal Bounds: {f_date(self._season[0])} - {f_date(self._season[1])}<br>"
                    #     f"Max Temporal Baseline: {self.temporal_baseline} days, Max Perpendicular Baseline: {self.perp_baseline}m<br>"
                    #     f"Stack Size: {len(insar_node_pairs)} pairs from {self.ref_stack_len()} scenes<br>"
                    # ),
                    y=0.95,
                    x=0.5,
                    xanchor="center",
                    yanchor="top",
                    font=dict(
                        family="Helvetica, monospace",
                        size=22,
                    ),
                ),
                plot_bgcolor="white",
                paper_bgcolor="lightgrey",
            ),
        )
        fig.show()


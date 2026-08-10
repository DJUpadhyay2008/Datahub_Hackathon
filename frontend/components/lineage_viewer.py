# ==============================================================================
# FILE: frontend/components/lineage_viewer.py
# WHY THIS FILE EXISTS:
#   Renders interactive visual lineage graphs (DAGs) in the Streamlit application.
# WHAT IT DOES:
#   1. Constructs a directed network graph (NetworkX) of upstream and downstream datasets.
#   2. Plots nodes (Datasets, Dashboards) and directed edges (Data transformations).
#   3. Highlights target dataset, input sources (Upstream), and dependent outputs (Downstream).
# HOW IT INTERACTS WITH DATAHUB:
#   Parses `upstreams` and `downstreams` metadata aspects returned from DataHub REST API.
# ==============================================================================

import streamlit as st
import networkx as nx
import plotly.graph_objects as go
from typing import Dict, Any, List

def render_lineage_dag(selected_table: str, all_datasets_dict: Dict[str, Any]):
    """Renders an interactive NetworkX + Plotly Lineage Directed Graph."""
    G = nx.DiGraph()

    # Pre-defined hierarchy layout positions for clean visualization
    positions = {
        "customers": (0, 1),
        "products": (0, -1),
        "orders": (1, 1),
        "inventory": (1, -1),
        "reviews": (1, -2),
        "order_items": (2, 2),
        "payments": (2, 0),
        "sales_report": (3, 0.5),
        "revenue_dashboard": (4, 0.5)
    }

    # Add all nodes and directed edges
    for name, item in all_datasets_dict.items():
        G.add_node(name, platform=item.get("platform", "postgres"))
        
        for down_urn in item.get("downstreams", []):
            down_name = down_urn.split(".")[-1].replace(",PROD)", "")
            G.add_edge(name, down_name)

    # Calculate layout if position not manually set
    pos = {}
    for node in G.nodes():
        if node in positions:
            pos[node] = positions[node]
        else:
            pos[node] = (2, 0)

    # Edge traces
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color="#64748b"),
        hoverinfo='none',
        mode='lines'
    )

    # Node traces
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    node_sizes = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"<b>{node}</b><br>Type: {G.nodes[node].get('platform', 'postgres')}")
        
        # Color coding
        if node == selected_table:
            node_colors.append("#ec4899")  # Bright Pink for selected target
            node_sizes.append(40)
        elif node in ["sales_report", "revenue_dashboard"]:
            node_colors.append("#8b5cf6")  # Purple for Reporting / BI
            node_sizes.append(35)
        else:
            node_colors.append("#3b82f6")  # Blue for Source tables
            node_sizes.append(30)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=[n for n in G.nodes()],
        textposition="bottom center",
        marker=dict(
            showscale=False,
            color=node_colors,
            size=node_sizes,
            line_width=2,
            line=dict(color='#ffffff')
        )
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(text=f"Lineage Graph for '{selected_table}'", font=dict(size=18, color="#ffffff")),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=20, r=20, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(15, 23, 42, 0.8)',
            paper_bgcolor='rgba(15, 23, 42, 0.0)',
            height=400
        )
    )

    st.plotly_chart(fig, use_container_width=True)

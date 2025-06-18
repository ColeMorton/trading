import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path for imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.cluster.hierarchy import dendrogram, leaves_list, linkage
from scipy.spatial.distance import squareform

PORTFOLIO = ["MSTR", "BTC-USD", "TSLA", "ALGN", "USB", "CLSK", "COR", "AMAT", "NFLX"]

# PORTFOLIO = ['SPY', 'QQQ']

NEXT = ["AMZN", "CEG", "CSCO", "DKNG", "GOOG", "IRM", "LYV", "META", "SCHW", "VRSN"]

# NEXT = [
#     'BTC-USD',
#   "XMR-USD",
#   "LTC-USD",
#   "TRX-USD"
# ]

ASSETS = list(dict.fromkeys(PORTFOLIO + NEXT))  # Remove duplicates

DAYS = 60


def create_dendrogram_trace(linkage_matrix, labels):
    """Create a dendrogram trace using scipy's dendrogram function."""
    # Create dendrogram data
    dn = dendrogram(linkage_matrix, labels=labels, no_plot=True)

    # Extract positions of each label
    x_coords = []
    y_coords = []
    for i, d in zip(dn["icoord"], dn["dcoord"]):
        x_coords.extend(i)
        y_coords.extend(d)
        x_coords.append(None)
        y_coords.append(None)

    return go.Scatter(
        x=x_coords, y=y_coords, mode="lines", line=dict(color="black"), hoverinfo="none"
    )


def generate_correlation_plot(assets, days, title_suffix=""):
    """Generate correlation heatmap and dendrogram for given assets.

    Args:
        assets (list): List of asset symbols
        days (int): Number of days for historical data
        title_suffix (str): Additional text for title

    Returns:
        tuple: (dendrogram figure, heatmap figure)
    """
    datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Download data
    import pandas as pd
    import polars as pl

    from app.tools.download_data import download_data

    all_data = {}
    date_ranges = []
    for asset in assets:
        config = {"PERIOD": f"{days}d"}
        df: pl.DataFrame = download_data(asset, config, print)
        pandas_df = df.to_pandas()
        all_data[asset] = pandas_df["Close"]
        date_ranges.append(pandas_df.index)

    # Find the intersection of all date ranges
    common_dates = date_ranges[0]
    for dr in date_ranges[1:]:
        common_dates = common_dates.intersection(dr)

    # Reindex each series to the common date range
    for asset in assets:
        all_data[asset] = all_data[asset].reindex(common_dates)

    data = pd.DataFrame(all_data)

    # Calculate daily returns
    returns = data.pct_change(fill_method=None).dropna()

    # Calculate correlation matrix
    correlation_matrix = returns.corr()

    # Perform hierarchical clustering
    distance_matrix = 1 - correlation_matrix
    condensed_dist = squareform(distance_matrix)
    Z = linkage(condensed_dist, method="ward")

    # Create dendrogram figure
    dendro_trace = create_dendrogram_trace(Z, assets)
    dendro_fig = go.Figure(data=[dendro_trace])
    dendro_fig.update_layout(
        title=f"Dendrogram of Asset Correlation{title_suffix}",
        height=300,  # Reduced height
        xaxis={
            "tickangle": 45,
            "ticktext": assets,
            "tickvals": list(range(len(assets))),
            "tickfont": {"size": 10},  # Smaller tick labels
        },
        margin=dict(t=50, b=30, l=50, r=50),  # Tighter margins
        font=dict(size=10),  # Consistent font size
    )

    # Reorder correlation matrix based on clustering
    ordered_assets = [assets[idx] for idx in leaves_list(Z)]
    reordered_correlation_matrix = correlation_matrix.loc[
        ordered_assets, ordered_assets
    ]

    # Create heatmap
    heatmap_fig = go.Figure(
        data=go.Heatmap(
            z=reordered_correlation_matrix,
            x=reordered_correlation_matrix.index,
            y=reordered_correlation_matrix.columns,
            zmin=-1,
            zmax=1,
            text=np.round(reordered_correlation_matrix, 2),
            texttemplate="%{text}",
            textfont={"size": 9},  # Slightly smaller text
            colorscale="RdBu",
            showscale=True,
            hoverongaps=False,  # Disable hover on gaps
            hoverlabel=dict(font_size=10),  # Consistent hover text size
        )
    )
    heatmap_fig.update_layout(
        title=f"Asset Correlation Matrix ({days}-day look-back){title_suffix}",
        height=600,  # Reduced height
        xaxis={"tickangle": 45, "tickfont": {"size": 9}},  # Smaller tick labels
        yaxis={
            "autorange": "reversed",
            "tickfont": {"size": 9},
        },  # Ensure heatmap matches dendrogram order
        margin=dict(t=50, b=30, l=50, r=50),  # Tighter margins
    )

    return dendro_fig, heatmap_fig


# Calculate total number of rows needed (2 for all assets + 2 for each NEXT asset)
total_rows = 2 + (2 * len(NEXT))

# Create main figure with subplots
main_fig = make_subplots(
    rows=total_rows,
    cols=1,
    subplot_titles=[
        "Dendrogram (All Assets)",
        "Correlation Matrix (All Assets)",
    ]
    + [
        item
        for asset in NEXT
        for item in [
            f"Dendrogram (Portfolio + {asset})",
            f"Correlation Matrix (Portfolio + {asset})",
        ]
    ],
    vertical_spacing=0.02,  # Reduced spacing between subplots
    specs=[[{"type": "scatter"}] for _ in range(total_rows)],
    row_heights=[
        0.4 if i % 2 == 0 else 1 for i in range(total_rows)
    ],  # Taller heatmaps, shorter dendrograms
)

# Generate plot for PORTFOLIO + NEXT (all assets)
dendro1, heatmap1 = generate_correlation_plot(ASSETS, DAYS, " (All Assets)")
main_fig.add_trace(dendro1.data[0], row=1, col=1)
main_fig.add_trace(heatmap1.data[0], row=2, col=1)

# Generate individual plots for each NEXT asset
for i, next_asset in enumerate(NEXT):
    portfolio_plus_asset = list(
        dict.fromkeys(PORTFOLIO + [next_asset])
    )  # Remove duplicates
    dendro, heatmap = generate_correlation_plot(
        portfolio_plus_asset, DAYS, f" (Portfolio + {next_asset})"
    )
    main_fig.add_trace(dendro.data[0], row=2 * i + 3, col=1)
    main_fig.add_trace(heatmap.data[0], row=2 * i + 4, col=1)

# Update layout
main_fig.update_layout(
    height=total_rows * 400,  # Reduced height per subplot
    width=None,  # Allow width to be determined by browser window
    showlegend=False,
    title_text="Portfolio Correlation Analysis",
    template="plotly_white",
    margin=dict(t=80, b=30, l=50, r=50),  # Reduced margins
    font=dict(size=10),  # Smaller font size for better compactness
)

# Update subplot heights
for i in range(total_rows):
    if i % 2 == 0:  # Dendrogram
        main_fig.update_xaxes(row=i + 1, col=1, tickangle=45)
        main_fig.update_yaxes(row=i + 1, col=1, range=[0, 2])
    else:  # Heatmap
        main_fig.update_xaxes(row=i + 1, col=1, tickangle=45)
        main_fig.update_yaxes(row=i + 1, col=1, autorange="reversed")

# Save to HTML file with full width configuration
output_path = os.path.join(os.getcwd(), "correlation_analysis.html")
main_fig.write_html(
    output_path,
    full_html=True,
    include_plotlyjs=True,
    config={
        "responsive": True,
        "displayModeBar": True,
        "scrollZoom": True,
    },
)

# Register and use Brave browser
import webbrowser

try:
    # Register Brave browser
    brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    webbrowser.register("brave", None, webbrowser.BackgroundBrowser(brave_path))
    # Open file in Brave
    webbrowser.get("brave").open("file://" + output_path)
except Exception as e:
    print(f"Error opening in Brave: {e}")
    # Fallback to default browser if Brave registration fails

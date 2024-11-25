import yfinance as yf
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import gridspec
from datetime import datetime, timedelta
from scipy.cluster.hierarchy import linkage, dendrogram, leaves_list
from scipy.spatial.distance import squareform
import numpy as np

# ASSETS = ['BTC-USD', 'SPY', 'DFS', 'FAST', 'AAPL', 'AKAM', 'TSLA', 'AMD', 'SLV', 'MPWR', 'TER', 'HNI', 'ICE', 'VLTO', 'ISRG', 'CINF', 'GRMN', 'TYL', 'ODFL', 'PANW']

ASSETS = ['SOL-USD', 'BTC-USD', 'HES', 'FDS', 'CHD', 'VLO', 'CMG', 'ALGN', 'CB', 'EW', 'DPZ', 'NXPI', 'CSX']

# ASSETS = ['BTC-USD', 'SPY', 'QQQ', 'SOL-USD', 'MSTR']

# ASSETS = ['BTC-USD', 'WLD-USD', 'SC-USD', 'RSR-USD', 'AERGO-USD', 'UNI-USD', 'AGLD-USD']

# ASSETS = ['MSTR', 'CORZ', 'WULF', 'HUT', 'MARA', 'CLSK', 'CIFR', 'BTC-USD', 'SPY', 'QQQ']

# 292 bars per year
# DAYS = 292

DAYS = 60

end_date = datetime.today().strftime('%Y-%m-%d')
start_date = (datetime.today() - timedelta(days=DAYS)).strftime('%Y-%m-%d')

# Download data
data = yf.download(ASSETS, start=start_date, end=end_date)['Adj Close']

# Step 3: Calculate daily returns
# Setting fill_method=None to avoid the FutureWarning
returns = data.pct_change(fill_method=None).dropna()

# Step 4: Calculate the correlation matrix
correlation_matrix = returns.corr()

# Step 5: Perform hierarchical clustering
# Compute the linkage matrix using correlation as distance
distance_matrix = 1 - correlation_matrix

# Convert the distance matrix to a condensed form to avoid the ClusterWarning
condensed_distance = squareform(distance_matrix, checks=False)

# Use the condensed distance matrix for linkage
linkage_matrix = linkage(condensed_distance, method='average')

# Step 6: Reorder the correlation matrix based on the clustering
ordered_assets = leaves_list(linkage_matrix)
reordered_correlation_matrix = correlation_matrix.iloc[ordered_assets, ordered_assets]

# Step 7: Plot the heatmap and dendrogram side by side
fig = plt.figure(figsize=(15, 8))

# Create a grid layout with 2 rows and 1 column, height ratios for dendrogram and heatmap
gs = gridspec.GridSpec(2, 1, height_ratios=[1, 3])

# Plot the dendrogram at the top (1st row)
ax_dendro = fig.add_subplot(gs[0])
dendrogram(linkage_matrix, labels=np.array(ASSETS)[ordered_assets], leaf_rotation=90)
ax_dendro.set_yticklabels([])  # Hide y-axis labels to make it cleaner
plt.title("Dendrogram of Asset Correlation")

# Plot the heatmap at the bottom (2nd row)
ax_heatmap = fig.add_subplot(gs[1])
sns.heatmap(reordered_correlation_matrix, annot=True, cmap="coolwarm", linewidths=.5, vmin=-1, vmax=1, ax=ax_heatmap)

# Title for the heatmap
plt.title(f'Asset Correlation Matrix with Hierarchical Clustering ({DAYS}-day look-back)')

# Adjust the layout so that there's no overlap between plots
plt.tight_layout()

# Show the combined plot
plt.show()

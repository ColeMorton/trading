import yfinance as yf
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from scipy.cluster.hierarchy import linkage, dendrogram, leaves_list
from scipy.spatial.distance import squareform
import numpy as np

ASSETS = ['BLDR', 'LLY', 'BTC-USD', 'SPY', 'MPC', 'EOG', 'AUDHKD=X']

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
# The correlation values are converted to distances as (1 - correlation)
distance_matrix = 1 - correlation_matrix

# Convert the distance matrix to a condensed form to avoid the ClusterWarning
condensed_distance = squareform(distance_matrix, checks=False)

# Use the condensed distance matrix for linkage
linkage_matrix = linkage(condensed_distance, method='average')

# Step 6: Reorder the correlation matrix based on the clustering
# Get the order of the assets after clustering
ordered_assets = leaves_list(linkage_matrix)

# Reorder the correlation matrix based on the clustering
reordered_correlation_matrix = correlation_matrix.iloc[ordered_assets, ordered_assets]

# Step 7: Visualize the reordered correlation matrix with hierarchical clustering
plt.figure(figsize=(12, 8))

# Draw the heatmap with the reordered correlation matrix
sns.heatmap(reordered_correlation_matrix, annot=True, cmap="coolwarm", linewidths=.5, vmin=-1, vmax=1)

# Title for the heatmap
plt.title(f'Asset Correlation Matrix with Hierarchical Clustering ({DAYS}-day look-back)')
plt.show()

# Optional: Visualize the dendrogram
plt.figure(figsize=(10, 5))
dendrogram(linkage_matrix, labels=np.array(ASSETS)[ordered_assets], leaf_rotation=90)
plt.title("Dendrogram of Asset Correlation")
plt.show()

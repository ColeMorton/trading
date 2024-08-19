import yfinance as yf
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

ASSETS = ['BLDR','LLY','BTC-USD', 'SPY', 'MPC', 'EOG', 'AUDHKD=X']

# 292 bars per year
# DAYS = 292

DAYS = 60

end_date = datetime.today().strftime('%Y-%m-%d')
start_date = (datetime.today() - timedelta(days=DAYS)).strftime('%Y-%m-%d')

# Download data
data = yf.download(ASSETS, start=start_date, end=end_date)['Adj Close']

# Step 3: Calculate daily returns
returns = data.pct_change().dropna()

# Step 4: Calculate the correlation matrix
correlation_matrix = returns.corr()

# Step 5: Visualize the correlation matrix
# Set up the matplotlib figure
plt.figure(figsize=(12, 8))

# Draw the heatmap with the mask and correct aspect ratio
sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", linewidths=.5, vmin=-1, vmax=1)

# Title for the heatmap
plt.title(f'Asset Correlation Matrix ({DAYS}-day look-back)')
plt.show()
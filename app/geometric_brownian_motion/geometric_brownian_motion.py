import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import os
from app.utils import download_data

BASE_DIR = 'C:/Projects/trading'

TICKER = 'BTC-USD'
ANNUAL_TRADING_DAYS = 365

T = 1  # Time horizon (in years)
dt = 0.01  # Time step (in years)
n_steps = int(T / dt)  # Number of time steps
n_simulations = 1000  # Number of simulations

# Download BTC-USD data
data = download_data(TICKER)

# Calculate required fields
initial_price = data["Close"][0]
returns = data["Close"].pct_change().drop_nulls()
drift = returns.mean() * ANNUAL_TRADING_DAYS  # Annualized return
volatility = returns.std() * np.sqrt(ANNUAL_TRADING_DAYS)  # Annualized standard deviation

gbm_params = pl.DataFrame({
    "Initial Price": [initial_price],
    "Drift (Annualized Return)": [drift],
    "Volatility (Annualized Std Dev)": [volatility]
})

print(gbm_params)

# Simulate simulations
simulations = np.zeros((n_simulations, n_steps))
simulations[:, 0] = initial_price

for i in range(1, n_steps):
    Z = np.random.standard_normal(n_simulations)  # Random shocks (Wiener process)
    simulations[:, i] = simulations[:, i - 1] * np.exp((drift - 0.5 * volatility**2) * dt + volatility * np.sqrt(dt) * Z)

# Plot the simulated simulations
plt.figure(figsize=(10, 6))
plt.plot(simulations.T, lw=0.5)
plt.title('Geometric Brownian Motion Simulated Simulations')
plt.xlabel('Time Steps')
plt.ylabel('Price')
plt.savefig(os.path.join(BASE_DIR, f'images/geometric_brownian_motion/{TICKER}_geometric_brownian_motion.png'))
plt.close()

# Convert simulations to a polars DataFrame
df = pl.DataFrame(simulations.T)

# Add a timestamp column
timestamps = pl.date_range(start=data["Date"].max(), end=data["Date"].max() + pl.duration(days=n_steps-1), eager=True)
df = df.with_columns(pl.Series("Timestamp", timestamps))

# Reorder columns to have Timestamp as the first column
columns = df.columns
df = df.select(["Timestamp"] + [col for col in columns if col != "Timestamp"])

# Export to CSV
csv_path = os.path.join(BASE_DIR, f'csv/geometric_brownian_motion/{TICKER}_geometric_brownian_motion_simulations.csv')
df.write_csv(csv_path)

print(f"{len(simulations)} GBM simulations exported to {csv_path}")

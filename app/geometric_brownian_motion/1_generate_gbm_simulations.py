import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import os
from app.utils import get_data

# Configuration
TICKER_1 = 'SPY'  # Ticker for X to USD exchange rate
TICKER_2 = 'BTC-USD'  # Ticker for Y to USD exchange rate
YEARS = 30  # Set timeframe in years for data
PERIOD = 'max' # Set time period for maximum data
USE_HOURLY = False  # Set to False for data
USE_SYNTHETIC = False  # Toggle between synthetic and original ticker
BASE_DIR = 'C:/Projects/trading'
TIME_HORIZON = 10 #Time horizon (in years)
SIMULATIONS = 1000

ANNUAL_TRADING_DAYS = 365
# ANNUAL_TRADING_DAYS = 252

# Default Configuration
CONFIG_DEFAULT = {
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "USE_SYNTHETIC": False,
    "TICKER_1": TICKER_1,
    "TICKER_2": TICKER_2,
    "BASE_DIR": BASE_DIR,
    "ANNUAL_TRADING_DAYS": 252,
    "TIME_HORIZON": 1,
    "SIMULATIONS": 1000
}

# Custom Configuration
CONFIG_CUSTOM = {
    "PERIOD": PERIOD,
    "USE_HOURLY": USE_HOURLY,
    "USE_SYNTHETIC": USE_SYNTHETIC,
    "TICKER_1": TICKER_1,
    "TICKER_2": TICKER_2,
    "BASE_DIR": BASE_DIR,
    "ANNUAL_TRADING_DAYS": ANNUAL_TRADING_DAYS,
    "TIME_HORIZON": TIME_HORIZON,
    "SIMULATIONS": SIMULATIONS
}

CONFIG = CONFIG_CUSTOM

dt = 0.00273972602  # Time step (in years)
n_steps = int(CONFIG['TIME_HORIZON'] / dt)  # Number of time steps

# Download BTC-USD data
data = get_data(CONFIG)

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
simulations = np.zeros((CONFIG['SIMULATIONS'], n_steps))
simulations[:, 0] = initial_price

for i in range(1, n_steps):
    Z = np.random.standard_normal(CONFIG['SIMULATIONS'])  # Random shocks (Wiener process)
    simulations[:, i] = simulations[:, i - 1] * np.exp((drift - 0.5 * volatility**2) * dt + volatility * np.sqrt(dt) * Z)

# Plot the simulated simulations
plt.figure(figsize=(10, 6))
plt.plot(simulations.T, lw=0.5)
plt.title('Geometric Brownian Motion Simulated Simulations')
plt.xlabel('Time Steps')
plt.ylabel('Price')
plt.savefig(os.path.join(BASE_DIR, f'images/geometric_brownian_motion/{CONFIG['TICKER_1']}_geometric_brownian_motion.png'))
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
csv_path = os.path.join(BASE_DIR, f'csv/geometric_brownian_motion/{CONFIG['TICKER_1']}_gbm_simulations.csv')
df.write_csv(csv_path)

print(f"{len(simulations)} GBM simulations exported to {csv_path}")

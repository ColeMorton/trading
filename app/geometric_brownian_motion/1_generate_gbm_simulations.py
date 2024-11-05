import polars as pl
import numpy as np
import matplotlib.pyplot as plt
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.utils import get_path, get_filename, save_csv

# Default Configuration
CONFIG = {
    "YEARS": 8.8,
    "USE_YEARS": True,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "TICKER": 'MSTR',
    "USE_SYNTHETIC": False,
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'SPY',
    "SHORT_WINDOW": 33,
    "LONG_WINDOW": 46,
    "SHORT": False,
    "USE_GBM": True,
    "USE_SMA": True,
    "BASE_DIR": 'C:/Projects/trading',
    "WINDOWS": 55,
    "ANNUAL_TRADING_DAYS": 365,
    "TIME_HORIZON": 4.44,
    "SIMULATIONS": 1000
}

config = get_config(CONFIG)

config["USE_GBM"] = True

dt = 0.00273972602  # Time step (in years)
n_steps = int(config['TIME_HORIZON'] / dt)  # Number of time steps

# Download BTC-USD data
data = get_data(config["TICKER"], config)

# Calculate required fields
initial_price = data["Close"][0]
returns = data["Close"].pct_change().drop_nulls()
drift = returns.mean() * config["ANNUAL_TRADING_DAYS"]  # Annualized return
volatility = returns.std() * np.sqrt(config["ANNUAL_TRADING_DAYS"])  # Annualized standard deviation

gbm_params = pl.DataFrame({
    "Initial Price": [initial_price],
    "Drift (Annualized Return)": [drift],
    "Volatility (Annualized Std Dev)": [volatility]
})

print(gbm_params)

# Simulate simulations
simulations = np.zeros((config['SIMULATIONS'], n_steps))
simulations[:, 0] = initial_price

for i in range(1, n_steps):
    Z = np.random.standard_normal(config['SIMULATIONS'])  # Random shocks (Wiener process)
    simulations[:, i] = simulations[:, i - 1] * np.exp((drift - 0.5 * volatility**2) * dt + volatility * np.sqrt(dt) * Z)

# Plot the simulated simulations
plt.figure(figsize=(10, 6))
plt.plot(simulations.T, lw=0.5)
plt.title('Geometric Brownian Motion Simulated Simulations')
plt.xlabel('Time Steps')
plt.ylabel('Price')
png_path = get_path("png", "geometric_brownian_motion", config, 'simulations')
png_filename = get_filename("png", config)
plt.savefig(png_path + "/" + png_filename)

plt.close()

# Convert simulations to a polars DataFrame
df = pl.DataFrame(simulations.T)

# Add a timestamp column
timestamps = pl.date_range(start=data["Date"].max(), end=data["Date"].max() + pl.duration(days=n_steps-1), eager=True)
df = df.with_columns(pl.Series("Timestamp", timestamps))

# Reorder columns to have Timestamp as the first column
columns = df.columns
df = df.select(["Timestamp"] + [col for col in columns if col != "Timestamp"])

# Save full data to CSV
save_csv(df, "geometric_brownian_motion", config, 'simulations')

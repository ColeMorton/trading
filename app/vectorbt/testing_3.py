import numpy as np
import pandas as pd
import vectorbt as vbt

# Define the function to calculate the Hurst Exponent
def hurst_exponent(time_series):
    """Returns the Hurst Exponent of the time series"""
    lags = range(2, 100)
    tau = [np.std(np.subtract(time_series[lag:], time_series[:-lag])) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0]*2.0

# Example of usage with vectorbt
# Pull data with vectorbt
data = vbt.YFData.download("BTC-USD", period="1y").get("Close")

# Calculate the Hurst Exponent
hurst_value = hurst_exponent(data.values)

print("Hurst Exponent:", hurst_value)

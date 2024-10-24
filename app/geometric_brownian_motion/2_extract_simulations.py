import csv
from io import StringIO
import numpy as np
import pandas as pd
from typing import List, Tuple

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

def read_csv_data(csv_content: str) -> Tuple[List[str], List[List[float]]]:
    csv_file = StringIO(csv_content)
    csv_reader = csv.reader(csv_file)
    header = next(csv_reader)  # Read header

    timestamps = []
    prices = [[] for _ in range(len(header) - 1)]  # Initialize lists for each simulation

    for row in csv_reader:
        timestamps.append(row[0])
        for i, price in enumerate(row[1:]):
            prices[i].append(float(price))

    return timestamps, prices

def calculate_performance(prices: List[float]) -> float:
    return (prices[-1] - prices[0]) / prices[0] * 100

def extract_simulations(csv_content: str) -> Tuple[dict, pd.DataFrame]:
    timestamps, simulations = read_csv_data(csv_content)
    performances = [calculate_performance(sim) for sim in simulations]
    
    num_simulations = len(simulations)
    print(f"Number of simulations: {num_simulations}")
    print(f"Length of timestamps: {len(timestamps)}")
    print(f"Length of first simulation: {len(simulations[0])}")
    
    if num_simulations <= 6:
        # If 6 or fewer simulations, export all of them
        results = {f"simulation_{i+1}_performance": perf for i, perf in enumerate(performances)}
        df_dict = {"timestamp": timestamps}
        for i, sim in enumerate(simulations):
            df_dict[f"simulation_{i+1}"] = sim
        df = pd.DataFrame(df_dict)
    else:
        # If 7 or more simulations, export the specific 6 simulations
        results = {
            "highest_performance": max(performances),
            "lowest_performance": min(performances),
            "mean_performance": np.mean(performances),
            "median_performance": np.median(performances),
            "25th_percentile_performance": np.percentile(performances, 25),
            "75th_percentile_performance": np.percentile(performances, 75)
        }
        
        # Extract the simulations
        highest_sim = simulations[performances.index(max(performances))]
        lowest_sim = simulations[performances.index(min(performances))]
        mean_sim = simulations[performances.index(min(performances, key=lambda x: abs(x - np.mean(performances))))]
        median_sim = simulations[performances.index(min(performances, key=lambda x: abs(x - np.median(performances))))]
        percentile_25_sim = simulations[performances.index(min(performances, key=lambda x: abs(x - np.percentile(performances, 25))))]
        percentile_75_sim = simulations[performances.index(min(performances, key=lambda x: abs(x - np.percentile(performances, 75))))]
        
        df = pd.DataFrame({
            "timestamp": timestamps,
            "highest": highest_sim,
            "lowest": lowest_sim,
            "mean": mean_sim,
            "median": median_sim,
            "25th_percentile": percentile_25_sim,
            "75th_percentile": percentile_75_sim
        })
    
    df.set_index("timestamp", inplace=True)
    return results, df

# Read the CSV file
with open(f'csv/geometric_brownian_motion/{CONFIG['TICKER_1']}_gbm_simulations.csv', 'r') as file:
    csv_content = file.read()

# Extract simulations
results, simulations_df = extract_simulations(csv_content)

# Print results
print("Extracted Simulations:")
for key, value in results.items():
    print(f"{key}: {value:.2f}%")

print(simulations_df)

# Save the simulations to a CSV file
simulations_df.to_csv(f'csv/geometric_brownian_motion/{CONFIG['TICKER_1']}_gbm_extracted_simulations.csv')
print(f"Simulations saved to csv/geometric_brownian_motion/{CONFIG['TICKER_1']}_gbm_extracted_simulations.csv")
print(f"Number of rows in extracted simulations: {len(simulations_df)}")

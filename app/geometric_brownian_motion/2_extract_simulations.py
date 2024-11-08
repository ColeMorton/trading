import csv
from io import StringIO
import numpy as np
import polars as pl
from typing import List, Tuple
from app.tools.get_config import get_config
from app.utils import get_path, get_filename, save_csv

# Default Configuration
CONFIG = {
    "YEARS": 4.44,
    "USE_YEARS": True,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "TICKER": 'SOL-USD',
    "USE_SYNTHETIC": False,
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'SPY',
    "SHORT_WINDOW": 33,
    "LONG_WINDOW": 46,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": True,
    "BASE_DIR": 'C:/Projects/trading',
    "WINDOWS": 55,
    "ANNUAL_TRADING_DAYS": 365,
    "TIME_HORIZON": 8.88,
    "SIMULATIONS": 1000
}

config = get_config(CONFIG)

config["USE_GBM"] = False

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

def extract_simulations(csv_content: str) -> Tuple[dict, pl.DataFrame]:
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
        df = pl.DataFrame(df_dict)
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
        
        df = pl.DataFrame({
            "timestamp": timestamps,
            "highest": highest_sim,
            "lowest": lowest_sim,
            "mean": mean_sim,
            "median": median_sim,
            "25th_percentile": percentile_25_sim,
            "75th_percentile": percentile_75_sim
        })
    
    # Set timestamp as index by making it the first column
    df = df.with_columns(pl.col("timestamp").alias("Date")).select(
        ["Date"] + [col for col in df.columns if col != "timestamp"]
    )
    
    return results, df

# Read the CSV file
filename = get_filename("csv", config)
path = get_path("csv", "geometric_brownian_motion", config, 'simulations')
fullpath = f"{path}/{filename}"

with open(fullpath, 'r') as file:
    csv_content = file.read()

# Extract simulations
results, simulations_df = extract_simulations(csv_content)

# Print results
print("Extracted Simulations:")
for key, value in results.items():
    print(f"{key}: {value:.2f}%")

print(simulations_df)

save_csv(simulations_df, "geometric_brownian_motion", config, 'filtered_simulations')

# # Save the simulations to a CSV file
# simulations_df.to_csv(f'csv/geometric_brownian_motion/{config['TICKER']}_gbm_extracted_simulations.csv')
# print(f"Simulations saved to csv/geometric_brownian_motion/{config['TICKER']}_gbm_extracted_simulations.csv")
# print(f"Number of rows in extracted simulations: {len(simulations_df)}")

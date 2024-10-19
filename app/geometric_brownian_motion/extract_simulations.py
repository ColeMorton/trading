import csv
from io import StringIO
import numpy as np
from typing import List, Tuple

def read_csv_data(csv_content: str) -> Tuple[List[str], List[float], List[float]]:
    csv_file = StringIO(csv_content)
    csv_reader = csv.reader(csv_file)
    next(csv_reader)  # Skip header

    timestamps = []
    prices = []

    for row in csv_reader:
        timestamps.append(row[0])
        prices.append([float(price) for price in row[1:]])

    return timestamps, prices

def calculate_performance(prices: List[float]) -> float:
    return (prices[-1] - prices[0]) / prices[0] * 100

def generate_simulations(initial_price: float, mu: float, sigma: float, dt: float, T: int, num_simulations: int) -> List[List[float]]:
    num_steps = int(T / dt)
    simulations = []
    
    for _ in range(num_simulations):
        prices = [initial_price]
        for _ in range(num_steps):
            dW = np.random.normal(0, np.sqrt(dt))
            dS = mu * prices[-1] * dt + sigma * prices[-1] * dW
            prices.append(prices[-1] + dS)
        simulations.append(prices)
    
    return simulations

def extract_simulations(csv_content: str) -> dict:
    timestamps, prices = read_csv_data(csv_content)
    
    # Use the first two columns to estimate mu and sigma
    initial_price = prices[0][0]
    returns = np.log(np.array(prices)[1:, :2] / np.array(prices)[:-1, :2])
    mu = np.mean(returns) / (1/252)  # Assuming daily data, annualize
    sigma = np.std(returns) * np.sqrt(252)  # Annualize volatility
    
    dt = 1/252  # Daily time step
    T = len(timestamps) / 252  # Total time in years
    
    simulations = generate_simulations(initial_price, mu, sigma, dt, T, 1000)
    
    performances = [calculate_performance(sim) for sim in simulations]
    sorted_performances = sorted(performances)
    
    results = {
        "highest_performance": max(performances),
        "lowest_performance": min(performances),
        "mean_performance": np.mean(performances),
        "median_performance": np.median(performances),
        "75th_percentile_performance": np.percentile(performances, 75)
    }
    
    return results

# Read the CSV file
with open('csv/geometric_brownian_motion/BTC-USD_geometric_brownian_motion_simulations.csv', 'r') as file:
    csv_content = file.read()

# Extract simulations
results = extract_simulations(csv_content)

# Print results
print("Extracted Simulations:")
print(f"1. Highest performance: {results['highest_performance']:.2f}%")
print(f"2. Lowest performance: {results['lowest_performance']:.2f}%")
print(f"3. Mean performance: {results['mean_performance']:.2f}%")
print(f"4. Median performance: {results['median_performance']:.2f}%")
print(f"5. 75th percentile performance: {results['75th_percentile_performance']:.2f}%")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
import os

# Load GBM data
gbm_data = pd.read_csv('csv/geometric_brownian_motion/SOL-USD_gbm_simulations.csv')
gbm_data['Timestamp'] = pd.to_datetime(gbm_data['Timestamp'])
gbm_data.set_index('Timestamp', inplace=True)

# Extract parameters from GBM data
dt = (gbm_data.index[1] - gbm_data.index[0]).days / 365.0
num_steps = len(gbm_data)
num_simulations = 2  # We have two simulations in the original data

# Calculate returns for parameter estimation
returns = np.log(gbm_data / gbm_data.shift(1))
mu = returns.mean() / dt
sigma = returns.std() / np.sqrt(dt)

# Jump Diffusion Model parameters
lambda_jump = 0.5  # Average number of jumps per year
jump_mean = 0  # Mean of jump size
jump_std = 0.1  # Standard deviation of jump size

def jump_diffusion_model(S0, mu, sigma, lambda_jump, jump_mean, jump_std, dt, num_steps, num_simulations):
    # Generate Brownian motion
    dW = np.random.normal(0, np.sqrt(dt), size=(num_steps, num_simulations))
    
    # Generate jump process
    N = np.random.poisson(lambda_jump * dt, size=(num_steps, num_simulations))
    J = np.random.normal(jump_mean, jump_std, size=(num_steps, num_simulations))
    
    # Calculate price paths
    S = np.zeros((num_steps + 1, num_simulations))
    S[0] = S0
    
    for t in range(1, num_steps + 1):
        S[t] = S[t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * dW[t-1] + N[t-1] * J[t-1])
    
    return S

# Run Jump Diffusion Model
S0 = gbm_data.iloc[0]
jd_simulations = jump_diffusion_model(S0, mu, sigma, lambda_jump, jump_mean, jump_std, dt, num_steps-1, num_simulations)

# Create a DataFrame with the same index as the original GBM data
jd_df = pd.DataFrame(jd_simulations, index=gbm_data.index, columns=['JD_Sim_1', 'JD_Sim_2'])

# Plotting
plt.figure(figsize=(12, 6))
plt.plot(gbm_data.index, gbm_data['column_0'], label='GBM Sim 1', alpha=0.7)
plt.plot(gbm_data.index, gbm_data['column_1'], label='GBM Sim 2', alpha=0.7)
plt.plot(jd_df.index, jd_df['JD_Sim_1'], label='JD Sim 1', alpha=0.7)
plt.plot(jd_df.index, jd_df['JD_Sim_2'], label='JD Sim 2', alpha=0.7)

plt.title('Geometric Brownian Motion vs Jump Diffusion Model - SOL-USD')
plt.xlabel('Date')
plt.ylabel('Price')
plt.legend()
plt.grid(True)

# Create directory if it doesn't exist
os.makedirs('images/jump_diffusion', exist_ok=True)

# Save the plot
plt.savefig('images/jump_diffusion/SOL-USD_gbm_vs_jd.png')
plt.close()

print("Jump Diffusion Model simulation completed and plot saved.")

# Calculate and print some statistics
gbm_final_prices = gbm_data.iloc[-1]
jd_final_prices = jd_df.iloc[-1]

print("\nFinal Prices:")
print("GBM Simulation 1:", gbm_final_prices['column_0'])
print("GBM Simulation 2:", gbm_final_prices['column_1'])
print("JD Simulation 1:", jd_final_prices['JD_Sim_1'])
print("JD Simulation 2:", jd_final_prices['JD_Sim_2'])

print("\nMean Final Price:")
print("GBM:", gbm_final_prices.mean())
print("JD:", jd_final_prices.mean())

print("\nStandard Deviation of Final Prices:")
print("GBM:", gbm_final_prices.std())
print("JD:", jd_final_prices.std())

import os

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy.optimize import minimize
from scipy.stats import norm

from app.tools.get_data import download_data
from app.tools.setup_logging import setup_logging


log, log_close, _, _ = setup_logging(
    module_name="ma_cross", log_file="1_jump_diffusion.log"
)

TICKER = "SUI20947-USD"
USE_MERTON = False

# Fetch historical data
gbm_data = download_data(TICKER, log)

# Print data info for debugging
print("Data columns:")
print(gbm_data.columns)
print("\nData types:")
print(gbm_data.dtypes)
print("\nNon-null counts:")
print(gbm_data.null_count())

# Use 'Close' price for our analysis
close_prices = gbm_data["Close"].to_numpy()
dates = gbm_data["Date"].to_numpy()

# Extract parameters from historical data
dt = 1 / 365  # Assuming daily data
num_steps = len(close_prices) - 1
num_simulations = 1000

# Calculate returns for parameter estimation
returns = np.log(close_prices[1:] / close_prices[:-1])
mu = returns.mean() / dt
sigma = returns.std() / np.sqrt(dt)


def merton_jump_diffusion_model(
    S0, mu, sigma, lambda_jump, jump_mean, jump_std, dt, num_steps, num_simulations
):
    dW = np.random.normal(0, np.sqrt(dt), size=(num_steps, num_simulations))
    N = np.random.poisson(lambda_jump * dt, size=(num_steps, num_simulations))
    J = np.random.normal(jump_mean, jump_std, size=(num_steps, num_simulations))

    S = np.zeros((num_steps + 1, num_simulations))
    S[0] = S0

    for t in range(1, num_steps + 1):
        S[t] = S[t - 1] * np.exp(
            (
                mu
                - 0.5 * sigma**2
                - lambda_jump * (np.exp(jump_mean + 0.5 * jump_std**2) - 1)
            )
            * dt
            + sigma * dW[t - 1]
            + N[t - 1] * J[t - 1]
        )

    return S


def geometric_brownian_motion(S0, mu, sigma, dt, num_steps, num_simulations):
    dW = np.random.normal(0, np.sqrt(dt), size=(num_steps, num_simulations))

    S = np.zeros((num_steps + 1, num_simulations))
    S[0] = S0

    for t in range(1, num_steps + 1):
        S[t] = S[t - 1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * dW[t - 1])

    return S


def calculate_var(returns, confidence_level=0.95):
    return -np.percentile(returns, 100 * (1 - confidence_level))


def log_likelihood(params, returns, dt):
    mu, sigma, lambda_jump, jump_mean, jump_std = params
    len(returns)

    def pdf(x):
        normal = norm.pdf(
            x,
            (
                mu
                - 0.5 * sigma**2
                - lambda_jump * (np.exp(jump_mean + 0.5 * jump_std**2) - 1)
            )
            * dt,
            sigma * np.sqrt(dt),
        )
        jump = norm.pdf(
            x,
            (
                mu
                - 0.5 * sigma**2
                - lambda_jump * (np.exp(jump_mean + 0.5 * jump_std**2) - 1)
            )
            * dt
            + jump_mean,
            np.sqrt(sigma**2 * dt + jump_std**2),
        )
        return (1 - lambda_jump * dt) * normal + lambda_jump * dt * jump

    return -np.sum(np.log(pdf(returns)))


# Parameter estimation
initial_guess = [mu, sigma, 10, 0, 0.1]  # Increased lambda_jump for cryptocurrencies
bounds = [(None, None), (0, None), (0, None), (None, None), (0, None)]
result = minimize(log_likelihood, initial_guess, args=(returns, dt), bounds=bounds)

mu_est, sigma_est, lambda_jump_est, jump_mean_est, jump_std_est = result.x

print("Estimated parameters:")
print(f"mu: {mu_est:.4f}")
print(f"sigma: {sigma_est:.4f}")
print(f"lambda_jump: {lambda_jump_est:.4f}")
print(f"jump_mean: {jump_mean_est:.4f}")
print(f"jump_std: {jump_std_est:.4f}")

# Run simulations
S0 = close_prices[0]
if USE_MERTON:
    jd_simulations = merton_jump_diffusion_model(
        S0,
        mu_est,
        sigma_est,
        lambda_jump_est,
        jump_mean_est,
        jump_std_est,
        dt,
        num_steps,
        num_simulations,
    )
else:
    jd_simulations = geometric_brownian_motion(
        S0, mu_est, sigma_est, dt, num_steps, num_simulations
    )
gbm_simulations = geometric_brownian_motion(
    S0, mu_est, sigma_est, dt, num_steps, num_simulations
)

# Calculate returns
jd_returns = (jd_simulations[-1] - jd_simulations[0]) / jd_simulations[0]
gbm_returns = (gbm_simulations[-1] - gbm_simulations[0]) / gbm_simulations[0]

# Calculate VaR
jd_var = calculate_var(jd_returns)
gbm_var = calculate_var(gbm_returns)

# Plotting
plt.figure(figsize=(12, 6))
plt.plot(dates, close_prices, label="Historical", color="black", linewidth=2)
for i in range(5):  # Plot 5 simulations for each model
    plt.plot(
        dates,
        jd_simulations[:, i],
        label=f'{"Merton" if USE_MERTON else "GBM"} Sim {i+1}' if i == 0 else "",
        alpha=0.7,
    )
    plt.plot(
        dates,
        gbm_simulations[:, i],
        label=f"GBM Sim {i+1}" if i == 0 else "",
        alpha=0.7,
    )

plt.title(
    f'{"Merton Jump-Diffusion" if USE_MERTON else "Geometric Brownian Motion"} vs GBM Model - SOL-USD'
)
plt.xlabel("Date")
plt.ylabel("Price")
plt.legend()
plt.grid(True)

# Create directory if it doesn't exist
os.makedirs("png/jump_diffusion", exist_ok=True)

# Save the plot
plt.savefig(f"png/jump_diffusion/{TICKER}_merton_vs_gbm.png")
plt.close()

print("Merton Jump-Diffusion Model simulation completed and plot saved.")

# Calculate and print statistics
jd_final_prices = jd_simulations[-1]
gbm_final_prices = gbm_simulations[-1]

print("\nFinal Prices Statistics:")
print(f"{'Merton' if USE_MERTON else 'GBM'} Mean: {jd_final_prices.mean():.4f}")
print(f"{'Merton' if USE_MERTON else 'GBM'} Std Dev: {jd_final_prices.std():.4f}")
print(f"GBM Mean: {gbm_final_prices.mean():.4f}")
print(f"GBM Std Dev: {gbm_final_prices.std():.4f}")

print("\nValue at Risk (95% confidence):")
print(f"{'Merton' if USE_MERTON else 'GBM'} VaR: {jd_var:.4f}")
print(f"GBM VaR: {gbm_var:.4f}")

# Save results to CSV
results_df = pl.DataFrame(
    {
        "Metric": ["Final Price Mean", "Final Price Std Dev", "VaR (95%)"],
        "Merton Jump-Diffusion"
        if USE_MERTON
        else "GBM": [
            jd_final_prices.mean(),
            jd_final_prices.std(),
            jd_var,
        ],
        "Geometric Brownian Motion": [
            gbm_final_prices.mean(),
            gbm_final_prices.std(),
            gbm_var,
        ],
    }
)

# Create directory if it doesn't exist
os.makedirs("data/outputs/jump_diffusion", exist_ok=True)

results_df.write_csv(f"data/outputs/jump_diffusion/{TICKER}_model_comparison.csv")
print(f"\nResults saved to data/outputs/jump_diffusion/{TICKER}_model_comparison.csv")

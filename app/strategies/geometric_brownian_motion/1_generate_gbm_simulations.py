"""
Generate Geometric Brownian Motion (GBM) simulations for price data.

This module simulates price movements using GBM and saves the results
to both CSV files and visualization plots.
"""

import polars as pl
import numpy as np
import matplotlib.pyplot as plt
from typing import TypedDict, NotRequired
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.utils import get_path, get_filename
from app.tools.export_csv import export_csv
from app.tools.setup_logging import setup_logging


class GBMConfig(TypedDict):
    """Configuration type definition for GBM simulations.

    Required Fields:
        YEARS (float): Number of years for historical data
        USE_YEARS (bool): Whether to use years for data range
        PERIOD (str): Period for data retrieval ('max', '1y', etc.)
        USE_HOURLY (bool): Whether to use hourly data
        TICKER (str): Primary ticker symbol
        USE_SYNTHETIC (bool): Whether to use synthetic data
        TICKER_1 (str): First comparison ticker
        TICKER_2 (str): Second comparison ticker
        BASE_DIR (str): Base directory for file operations
        WINDOWS (int): Window size for calculations
        ANNUAL_TRADING_DAYS (int): Number of trading days per year
        TIME_HORIZON (float): Time horizon for simulations
        SIMULATIONS (int): Number of simulations to generate
    """
    YEARS: float
    USE_YEARS: bool
    PERIOD: str
    USE_HOURLY: bool
    TICKER: str
    USE_SYNTHETIC: bool
    TICKER_1: str
    TICKER_2: str
    BASE_DIR: str
    WINDOWS: int
    ANNUAL_TRADING_DAYS: int
    TIME_HORIZON: float
    SIMULATIONS: int


def calculate_gbm_parameters(data: pl.DataFrame) -> tuple[float, float, float, float]:
    """
    Calculate the parameters needed for GBM simulation.

    Args:
        data (pl.DataFrame): Historical price data

    Returns:
        tuple[float, float, float, float]: Initial price, drift, volatility, and time step

    Raises:
        ValueError: If data is empty or required columns are missing
    """
    if len(data) == 0:
        raise ValueError("Empty data provided")
    
    initial_price = data["Close"][0]
    returns = data["Close"].pct_change().drop_nulls()
    drift = returns.mean() * 365  # Annualized return
    volatility = returns.std() * np.sqrt(365)  # Annualized standard deviation
    dt = 0.00273972602  # Time step (in years)
    
    return initial_price, drift, volatility, dt


def generate_gbm_simulations(
    initial_price: float,
    drift: float,
    volatility: float,
    dt: float,
    n_steps: int,
    n_sims: int
) -> np.ndarray:
    """
    Generate GBM simulations using the specified parameters.

    Args:
        initial_price (float): Starting price
        drift (float): Annualized drift
        volatility (float): Annualized volatility
        dt (float): Time step
        n_steps (int): Number of time steps
        n_sims (int): Number of simulations

    Returns:
        np.ndarray: Matrix of simulated prices
    """
    simulations = np.zeros((n_sims, n_steps))
    simulations[:, 0] = initial_price

    for i in range(1, n_steps):
        Z = np.random.standard_normal(n_sims)
        simulations[:, i] = simulations[:, i - 1] * np.exp(
            (drift - 0.5 * volatility**2) * dt + volatility * np.sqrt(dt) * Z
        )
    
    return simulations


def plot_simulations(
    simulations: np.ndarray,
    config: GBMConfig,
    data: pl.DataFrame
) -> None:
    """
    Plot and save the GBM simulations.

    Args:
        simulations (np.ndarray): Matrix of simulated prices
        config (GBMConfig): Configuration dictionary
        data (pl.DataFrame): Original price data for timestamp reference
    """
    plt.figure(figsize=(10, 6))
    plt.plot(simulations.T, lw=0.5)
    plt.title('Geometric Brownian Motion Simulated Paths')
    plt.xlabel('Time Steps')
    plt.ylabel('Price')
    
    png_path = get_path("png", "geometric_brownian_motion", config, 'simulations')
    png_filename = get_filename("png", config)
    plt.savefig(f"{png_path}/{png_filename}")
    plt.close()


def save_simulations(
    simulations: np.ndarray,
    data: pl.DataFrame,
    n_steps: int,
    config: GBMConfig,
    log: callable
) -> None:
    """
    Save the simulations to a CSV file.

    Args:
        simulations (np.ndarray): Matrix of simulated prices
        data (pl.DataFrame): Original price data for timestamp reference
        n_steps (int): Number of time steps
        config (GBMConfig): Configuration dictionary
        log: Logging function
    """
    df = pl.DataFrame(simulations.T)
    timestamps = pl.date_range(
        start=data["Date"].max(),
        end=data["Date"].max() + pl.duration(days=n_steps-1),
        eager=True
    )
    df = df.with_columns(pl.Series("Timestamp", timestamps))
    
    # Reorder columns to have Timestamp first
    columns = df.columns
    df = df.select(["Timestamp"] + [col for col in columns if col != "Timestamp"])
    
    export_csv(df, "geometric_brownian_motion", config, 'simulations', log=log)


def main() -> bool:
    """
    Main function to generate GBM simulations.

    Returns:
        bool: True if execution successful, False otherwise
    """
    log, log_close, _, _ = setup_logging(
        'geometric_brownian_motion',
        '1_generate_gbm_simulations.log'
    )
    
    try:
        # Default configuration
        DEFAULT_CONFIG: GBMConfig = {
            "YEARS": 5,
            "USE_YEARS": False,
            "PERIOD": 'max',
            "USE_HOURLY": False,
            "TICKER": 'MSTR',
            "USE_SYNTHETIC": False,
            "TICKER_1": 'BTC-USD',
            "TICKER_2": 'SPY',
            "BASE_DIR": '.',
            "WINDOWS": 89,
            "ANNUAL_TRADING_DAYS": 365,
            "TIME_HORIZON": 5,
            "SIMULATIONS": 1000
        }
        
        config = get_config(DEFAULT_CONFIG)
        data = get_data(config["TICKER"], config, log)
        
        initial_price, drift, volatility, dt = calculate_gbm_parameters(data)
        n_steps = int(config['TIME_HORIZON'] / dt)
        
        log(f"Generating {config['SIMULATIONS']} simulations over {n_steps} steps")
        
        simulations = generate_gbm_simulations(
            initial_price,
            drift,
            volatility,
            dt,
            n_steps,
            config['SIMULATIONS']
        )
        
        plot_simulations(simulations, config, data)
        save_simulations(simulations, data, n_steps, config, log)
        
        log("Successfully completed GBM simulations")
        log_close()
        return True
        
    except Exception as e:
        log(f"Error in GBM simulation: {str(e)}", "error")
        log_close()
        raise


if __name__ == "__main__":
    main()

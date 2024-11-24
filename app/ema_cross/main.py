"""
EMA Cross Strategy Analysis Main Module

This module serves as the entry point for running various EMA cross strategy analyses.
It handles command-line argument parsing, data preparation, and analysis execution.
"""

import argparse
from typing import Literal, Union, Tuple
import polars as pl
from app.tools.get_data import download_data, use_synthetic
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_rsi import calculate_rsi
import importlib
from config import CONFIG, Config

AnalysisType = Literal["parameter_sensitivity", "rsi", "stop_loss", "protective_stop_loss", "review"]

def prepare_data(config: Config) -> Tuple[pl.DataFrame, str]:
    """
    Prepare data for analysis by downloading and preprocessing.

    Args:
        config (Config): Configuration dictionary containing data parameters

    Returns:
        Tuple[pl.DataFrame, str]: Tuple containing:
            - Preprocessed data with moving averages and RSI (if enabled)
            - Ticker symbol or synthetic pair name
    """
    # Prepare data based on configuration
    if config['USE_SYNTHETIC']:
        data, synthetic_ticker = use_synthetic(
            config['TICKER_1'], 
            config['TICKER_2'], 
            config['USE_HOURLY']
        )
    else:
        data = download_data(
            config['TICKER_1'], 
            config['YEARS'], 
            config['USE_HOURLY']
        )
        synthetic_ticker = config['TICKER_1']

    # Calculate moving averages
    data = calculate_mas(
        data, 
        config['EMA_FAST'], 
        config['EMA_SLOW'], 
        config['USE_SMA']
    )
    
    # Add RSI if enabled
    if config['USE_RSI']:
        data = calculate_rsi(data, config['RSI_PERIOD'])

    return data, synthetic_ticker

def run_analysis(analysis_type: AnalysisType, data: pl.DataFrame, ticker: str, config: Config) -> None:
    """
    Run the specified analysis type with prepared data.

    Args:
        analysis_type (AnalysisType): Type of analysis to run
        data (pl.DataFrame): Preprocessed price data with indicators
        ticker (str): Ticker symbol or synthetic pair name
        config (Config): Configuration dictionary
    """
    module = importlib.import_module(f"{analysis_type}")
    module.run_analysis(data, ticker, config)

def main() -> None:
    """
    Main entry point for the EMA Cross Strategy Analysis.
    
    Handles command-line argument parsing, data preparation, and analysis execution.
    Supports multiple types of analysis including parameter sensitivity, RSI analysis,
    stop loss optimization, and protective stop loss analysis.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(description="EMA Cross Strategy Analysis")
    parser.add_argument(
        "analysis",
        choices=["parameter_sensitivity", "rsi", "stop_loss", "protective_stop_loss", "review"],
        help="Type of analysis to run"
    )
    args = parser.parse_args()

    # Prepare data
    data, synthetic_ticker = prepare_data(CONFIG)

    # Run the selected analysis
    run_analysis(args.analysis, data, synthetic_ticker, CONFIG)

if __name__ == "__main__":
    main()

import concurrent.futures
from datetime import datetime, timedelta
from typing import List, Tuple, TypedDict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import vectorbt as vbt

from app.tools.data_types import DataConfig
from app.tools.download_data import download_data
from app.tools.setup_logging import setup_logging

# Set up logging
log, log_close, logger, _ = setup_logging("atr", "atr_analysis.log")


class ATRConfig(TypedDict):
    """Configuration type definition for ATR analysis.

    Required Fields:
        USE_HOURLY: Whether to use hourly data
        USE_SYNTHETIC: Whether to use synthetic ticker
        TICKER_1: Ticker for X to USD
        TICKER_2: Ticker for Y to USD
    """

    USE_HOURLY: bool
    USE_SYNTHETIC: bool
    TICKER_1: str
    TICKER_2: str


# Default configuration
DEFAULT_CONFIG: ATRConfig = {
    "USE_HOURLY": False,  # Set to False for daily data
    "USE_SYNTHETIC": False,  # Toggle between synthetic and original ticker
    "TICKER_1": "AMD",  # Ticker for X to USD
    "TICKER_2": "BTC-USD",  # Ticker for Y to USD
}

# Local download_data function removed in favor of centralized implementation


def calculate_atr(data: pd.DataFrame, length: int) -> pd.Series:
    """
    Calculate Average True Range (ATR) using vectorized operations.

    Args:
        data (pd.DataFrame): Price data with High, Low, Close columns
        length (int): ATR period length

    Returns:
        pd.Series: ATR values
    """
    # Ensure data has proper index
    if not isinstance(data.index, pd.DatetimeIndex):
        log(
            "Warning: Data index is not DatetimeIndex in calculate_atr. This may cause issues.",
            "warning",
        )

    # Vectorized calculation of true range components
    high_low = data["High"] - data["Low"]
    high_close = np.abs(data["High"] - data["Close"].shift())
    low_close = np.abs(data["Low"] - data["Close"].shift())

    # Create a DataFrame with the three components, ensuring it has the same
    # index as the input data
    ranges = pd.DataFrame(
        {"HL": high_low, "HC": high_close, "LC": low_close}, index=data.index
    )

    # Calculate the true range as the maximum of the three components
    true_range = ranges.max(axis=1)

    # Use pandas rolling mean for the ATR calculation
    atr = true_range.rolling(window=length).mean()

    # Ensure the result has the same index as the input data
    return pd.Series(atr.values, index=data.index)


def calculate_atr_trailing_stop(
    close: float,
    atr: float,
    multiplier: float,
    highest_since_entry: float,
    previous_stop: float,
) -> float:
    """
    Calculate ATR Trailing Stop.

    Args:
        close (float): Current close price
        atr (float): Current ATR value
        multiplier (float): ATR multiplier
        highest_since_entry (float): Highest price since entry
        previous_stop (float): Previous stop level

    Returns:
        float: New trailing stop level
    """
    potential_stop: float = close - (atr * multiplier)
    if np.isnan(previous_stop):
        return potential_stop
    new_stop: float = highest_since_entry - (atr * multiplier)
    return max(new_stop, previous_stop)


def generate_signals(
    data: pd.DataFrame, atr_length: int, atr_multiplier: float
) -> pd.DataFrame:
    """
    Generate trading signals based on ATR Trailing Stop using optimized operations.

    Args:
        data (pd.DataFrame): Price data
        atr_length (int): ATR length
        atr_multiplier (float): ATR multiplier

    Returns:
        pd.DataFrame: Data with signals
    """
    log(
        f"Generating signals with ATR length: {atr_length}, multiplier: {atr_multiplier}"
    )

    # Debug input data
    log(f"DEBUG: Input data shape: {data.shape}")
    log(f"DEBUG: Input data columns: {data.columns.tolist()}")
    log(f"DEBUG: Input data index type: {type(data.index)}")

    # Create a copy to avoid modifying the original
    data = data.copy()

    # Ensure data has a proper index
    if not isinstance(data.index, pd.DatetimeIndex):
        log(
            "Warning: Data index is not DatetimeIndex in generate_signals. Converting to DatetimeIndex.",
            "warning",
        )
        if "Date" in data.columns:
            data = data.set_index("Date")
        else:
            # Create a dummy datetime index if no date column exists
            data.index
            data = data.reset_index(drop=True)
            data.index = pd.date_range(start="2000-01-01", periods=len(data), freq="D")
            log(
                f"Created dummy DatetimeIndex for data with shape {data.shape}",
                "warning",
            )

    # Ensure all input columns are 1D arrays
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in data.columns:
            # Check if values are 2D and flatten if needed
            if hasattr(data[col].values, "shape") and len(data[col].values.shape) > 1:
                log(
                    f"DEBUG: Flattening {col} values from shape {data[col].values.shape}"
                )
                data[col] = pd.Series(data[col].values.flatten(), index=data.index)

    # Calculate ATR
    data["ATR"] = calculate_atr(data, atr_length)

    # Initialize columns with explicit 1D arrays
    data["Signal"] = pd.Series(np.zeros(len(data)), index=data.index)
    data["ATR_Trailing_Stop"] = pd.Series(np.full(len(data), np.nan), index=data.index)
    data["Highest_Since_Entry"] = pd.Series(
        np.full(len(data), np.nan), index=data.index
    )

    log(
        f"Data shape after initialization: {data.shape}, columns: {data.columns.tolist()}"
    )

    # Skip first row due to ATR calculation requiring previous values
    in_position = False

    # Process rows iteratively - this is more reliable than the fully
    # vectorized approach
    for i in range(1, len(data)):
        current_close = float(data["Close"].iloc[i])  # Ensure scalar value
        current_atr = float(data["ATR"].iloc[i])  # Ensure scalar value

        if not in_position:
            # Check for entry condition
            potential_stop = current_close - (current_atr * atr_multiplier)

            if current_close >= potential_stop:
                data.loc[data.index[i], "Signal"] = 1
                data.loc[data.index[i], "ATR_Trailing_Stop"] = potential_stop
                data.loc[data.index[i], "Highest_Since_Entry"] = current_close
                in_position = True
        else:
            # Update highest price since entry
            prev_highest = float(
                data["Highest_Since_Entry"].iloc[i - 1]
            )  # Ensure scalar value
            current_highest = max(prev_highest, current_close)
            data.loc[data.index[i], "Highest_Since_Entry"] = current_highest

            # Get previous stop
            prev_stop = float(
                data["ATR_Trailing_Stop"].iloc[i - 1]
            )  # Ensure scalar value

            # Calculate new trailing stop
            new_stop = max(current_highest - (current_atr * atr_multiplier), prev_stop)
            data.loc[data.index[i], "ATR_Trailing_Stop"] = new_stop

            # Check for exit condition
            if current_close < new_stop:
                data.loc[data.index[i], "Signal"] = 0
                in_position = False
            else:
                data.loc[data.index[i], "Signal"] = 1

    # Calculate position column
    data["Position"] = data["Signal"].shift()

    # Ensure all columns have the same index and are 1D arrays
    for col in data.columns:
        if isinstance(data[col], pd.Series):
            # Check if values are 2D and flatten if needed
            if hasattr(data[col].values, "shape") and len(data[col].values.shape) > 1:
                log(
                    f"DEBUG: Final flattening of {col} values from shape {data[col].values.shape}"
                )
                data[col] = pd.Series(data[col].values.flatten(), index=data.index)

    # Final check of data shapes
    log(f"DEBUG: Final data shape: {data.shape}")
    for col in data.columns:
        if hasattr(data[col].values, "shape"):
            log(f"DEBUG: Final {col} values shape: {data[col].values.shape}")

    return data


def backtest_strategy(data: pd.DataFrame) -> vbt.Portfolio:
    """
    Backtest the ATR Trailing Stop strategy.

    Args:
        data (pd.DataFrame): Price data with signals

    Returns:
        vbt.Portfolio: Portfolio object with backtest results

    Raises:
        ValueError: If data is empty or doesn't have required columns
    """
    # Debug input data
    log(f"DEBUG: backtest_strategy input data shape: {data.shape}")
    log(f"DEBUG: backtest_strategy input columns: {data.columns.tolist()}")

    # Validate input data
    if data.empty:
        raise ValueError("Input data is empty")

    required_columns = ["Close", "Signal"]
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Required column '{col}' not found in data")

    # Ensure data has proper index
    if not isinstance(data.index, pd.DatetimeIndex):
        log(
            "Warning: Data index is not DatetimeIndex. Converting to DatetimeIndex.",
            "warning",
        )
        if "Date" in data.columns:
            data = data.set_index("Date")
        else:
            # Create a dummy datetime index if no date column exists
            data = data.reset_index(drop=True)
            data.index = pd.date_range(start="2000-01-01", periods=len(data), freq="D")

    # Debug column shapes before processing
    for col in ["Close", "Signal"]:
        if hasattr(data[col].values, "shape"):
            log(
                f"DEBUG: {col} values shape before processing: {data[col].values.shape}"
            )
            # Ensure 1D
            if len(data[col].values.shape) > 1:
                log(f"DEBUG: Flattening {col} in backtest_strategy")
                data[col] = pd.Series(data[col].values.flatten(), index=data.index)

    # Pre-calculate entry and exit conditions for better performance
    entries = (data["Signal"] == 1) & (data["Signal"].shift(1) != 1)
    exits = (data["Signal"] == 0) & (data["Signal"].shift(1) == 1)

    # Debug entry/exit signals
    log(f"DEBUG: entries shape: {entries.shape}, dtype: {entries.dtype}")
    log(f"DEBUG: exits shape: {exits.shape}, dtype: {exits.dtype}")

    # Create portfolio with vectorized operations
    try:
        # Ensure all Series are 1-dimensional and have the same index
        # Extract values as 1D arrays to prevent dimensionality issues
        close_values = data["Close"].values
        entries_values = entries.values
        exits_values = exits.values

        # Debug values shapes
        log(
            f"DEBUG: close_values shape: {close_values.shape if hasattr(close_values, 'shape') else 'no shape'}"
        )
        log(
            f"DEBUG: entries_values shape: {entries_values.shape if hasattr(entries_values, 'shape') else 'no shape'}"
        )
        log(
            f"DEBUG: exits_values shape: {exits_values.shape if hasattr(exits_values, 'shape') else 'no shape'}"
        )

        # Flatten if needed
        if hasattr(close_values, "shape") and len(close_values.shape) > 1:
            log(f"DEBUG: Flattening close_values from shape {close_values.shape}")
            close_values = close_values.flatten()

        if hasattr(entries_values, "shape") and len(entries_values.shape) > 1:
            log(f"DEBUG: Flattening entries_values from shape {entries_values.shape}")
            entries_values = entries_values.flatten()

        if hasattr(exits_values, "shape") and len(exits_values.shape) > 1:
            log(f"DEBUG: Flattening exits_values from shape {exits_values.shape}")
            exits_values = exits_values.flatten()

        # Create Series with proper index and 1D values
        close_series = pd.Series(close_values, index=data.index)
        entries_series = pd.Series(entries_values, index=data.index)
        exits_series = pd.Series(exits_values, index=data.index)

        # Final debug check
        log(f"DEBUG: close_series shape: {close_series.shape}")
        log(f"DEBUG: entries_series shape: {entries_series.shape}")
        log(f"DEBUG: exits_series shape: {exits_series.shape}")

        portfolio: vbt.Portfolio = vbt.Portfolio.from_signals(
            close=close_series,
            entries=entries_series,
            exits=exits_series,
            init_cash=1000,
            fees=0.001,
        )
        return portfolio
    except Exception as e:
        log(f"Error in backtest_strategy: {str(e)}", "error")
        log(f"DEBUG: Exception type: {type(e)}")
        log(f"DEBUG: Exception args: {e.args}")

        # Return a dummy portfolio with zero returns if backtesting fails
        dummy_index = data.index
        dummy_close = pd.Series(100, index=dummy_index)
        dummy_entries = pd.Series(False, index=dummy_index)
        dummy_exits = pd.Series(False, index=dummy_index)

        dummy_portfolio = vbt.Portfolio.from_signals(
            close=dummy_close,
            entries=dummy_entries,
            exits=dummy_exits,
            init_cash=1000,
            fees=0.001,
        )
        return dummy_portfolio


def analyze_params(
    data: pd.DataFrame, atr_length: int, atr_multiplier: float
) -> Tuple[int, float, float]:
    """
    Analyze parameters for ATR trailing stop strategy.

    Args:
        data (pd.DataFrame): Price data
        atr_length (int): ATR length
        atr_multiplier (float): ATR multiplier

    Returns:
        Tuple[int, float, float]: ATR length, ATR multiplier, total return
    """
    log(f"Analyzing parameters: ATR length={atr_length}, multiplier={atr_multiplier}")

    try:
        # Generate signals with optimized function
        data_with_signals: pd.DataFrame = generate_signals(
            data.copy(), atr_length, atr_multiplier
        )

        # Debug information
        log(f"DEBUG: data_with_signals shape: {data_with_signals.shape}")
        log(f"DEBUG: data_with_signals index type: {type(data_with_signals.index)}")
        log(f"DEBUG: data_with_signals columns: {data_with_signals.columns.tolist()}")

        # Check for NaN values
        for col in ["Close", "Signal"]:
            nan_count = data_with_signals[col].isna().sum()
            log(f"DEBUG: NaN count in {col}: {nan_count}")

        # Check data types and shapes
        for col in ["Close", "Signal"]:
            log(f"DEBUG: {col} type: {type(data_with_signals[col])}")
            log(f"DEBUG: {col} shape: {data_with_signals[col].shape}")
            log(f"DEBUG: {col} values type: {type(data_with_signals[col].values)}")
            log(f"DEBUG: {col} values shape: {data_with_signals[col].values.shape}")

            # Ensure values are 1D
            if len(data_with_signals[col].values.shape) > 1:
                log(f"DEBUG: Flattening {col} values")
                data_with_signals[col] = pd.Series(
                    data_with_signals[col].values.flatten(),
                    index=data_with_signals.index,
                )

        # Backtest the strategy
        portfolio: vbt.Portfolio = backtest_strategy(data_with_signals)

        # Get total return as scalar value
        total_return_value = portfolio.total_return()

        # Debug information for total return
        log(f"DEBUG: total_return_value type: {type(total_return_value)}")
        if hasattr(total_return_value, "shape"):
            log(f"DEBUG: total_return_value shape: {total_return_value.shape}")

        # Convert to scalar if needed
        if isinstance(total_return_value, pd.Series):
            log(
                f"DEBUG: total_return_value is a Series with length {len(total_return_value)}"
            )
            if len(total_return_value) == 1:
                total_return_value = total_return_value.item()
                log(f"DEBUG: Converted to scalar: {total_return_value}")
            else:
                log(
                    f"Unexpected Series length: {len(total_return_value)}, using first value",
                    "warning",
                )
                total_return_value = float(total_return_value.iloc[0])
                log(f"DEBUG: Used first value: {total_return_value}")
        elif isinstance(total_return_value, (float, int)):
            # Already a scalar, no conversion needed
            log(f"DEBUG: total_return_value is already a scalar: {total_return_value}")
        else:
            # Handle other types by converting to float
            log(f"DEBUG: Converting unknown type to float")
            total_return_value = float(total_return_value)
            log(f"DEBUG: Converted value: {total_return_value}")

        return atr_length, atr_multiplier, total_return_value
    except Exception as e:
        log(f"Error in analyze_params: {str(e)}", "error")
        log(f"DEBUG: Exception type: {type(e)}")
        log(f"DEBUG: Exception args: {e.args}")
        raise


def parameter_sensitivity_analysis(
    data: pd.DataFrame, atr_lengths: List[int], atr_multipliers: List[float]
) -> pd.DataFrame:
    """
    Perform parameter sensitivity analysis with sequential processing for reliability.

    Args:
        data (pd.DataFrame): Price data
        atr_lengths (List[int]): List of ATR lengths to test
        atr_multipliers (List[float]): List of ATR multipliers to test

    Returns:
        pd.DataFrame: Results matrix with ATR lengths as index and ATR multipliers as columns
    """
    log(
        f"Starting parameter sensitivity analysis with {len(atr_lengths)} lengths and {len(atr_multipliers)} multipliers"
    )

    try:
        # Initialize results dictionary for safer assignment
        results_dict = {}

        # Calculate total combinations for progress tracking
        total_combinations = len(atr_lengths) * len(atr_multipliers)
        current_combination = 0

        # Process combinations sequentially for reliability
        for length in atr_lengths:
            results_dict[length] = {}

            for multiplier in atr_multipliers:
                current_combination += 1
                log(
                    f"Processing combination {current_combination}/{total_combinations}: length={length}, multiplier={multiplier}"
                )

                try:
                    # Analyze parameters
                    length_val, multiplier_val, total_return = analyze_params(
                        data.copy(), length, multiplier
                    )
                    log(
                        f"Result for length={length}, multiplier={multiplier}: total_return={total_return:.4f}"
                    )

                    # Store result in dictionary - ensure it's a float
                    results_dict[length][multiplier] = float(total_return)
                except Exception as e:
                    log(
                        f"Error analyzing params for length={length}, multiplier={multiplier}: {str(e)}",
                        "error",
                    )
                    # Store NaN for failed combinations
                    results_dict[length][multiplier] = np.nan
                    continue

        # Create a properly indexed DataFrame from the dictionary
        # First create a DataFrame with explicit index and columns
        results = pd.DataFrame(
            index=pd.Index(atr_lengths, name="ATR Length"),
            columns=pd.Index(atr_multipliers, name="ATR Multiplier"),
        )

        # Fill in the values from our dictionary
        for length in results_dict:
            for multiplier in results_dict[length]:
                results.loc[length, multiplier] = results_dict[length][multiplier]

        # Ensure all values are float
        results = results.astype(float)

        log(f"Completed parameter sensitivity analysis. Results shape: {results.shape}")
        log(f"DEBUG: Results dtypes: {results.dtypes}")
        return results
    except Exception as e:
        log(f"Error in parameter_sensitivity_analysis: {str(e)}", "error")
        raise


def plot_heatmap(results: pd.DataFrame, ticker: str, config: ATRConfig) -> None:
    """
    Plot heatmap of the parameter sensitivity analysis results.

    Args:
        results (pd.DataFrame): Results matrix with ATR lengths as index and ATR multipliers as columns
        ticker (str): Ticker symbol
        config (ATRConfig): Configuration dictionary
    """
    # Set style for better visualization
    sns.set_style("whitegrid")

    # Create figure with appropriate size
    plt.figure(figsize=(12, 8))

    # Ensure data is numeric
    log("DEBUG: Converting results to numeric values for heatmap")
    numeric_results = results.astype(float)

    log(f"DEBUG: Results shape: {numeric_results.shape}")
    log(f"DEBUG: Results dtypes: {numeric_results.dtypes}")
    log(f"DEBUG: Results index type: {type(numeric_results.index)}")
    log(f"DEBUG: Results columns type: {type(numeric_results.columns)}")

    # Create heatmap with improved aesthetics
    ax = sns.heatmap(
        numeric_results,
        annot=True,
        cmap="YlGnBu",
        fmt=".3f",
        linewidths=0.5,
        cbar_kws={"label": "Total Return"},
        annot_kws={"size": 10},
    )

    # Set title and labels with more information
    interval = "Hourly" if config["USE_HOURLY"] else "Daily"
    plt.title(
        f"ATR Trailing Stop Parameter Sensitivity - {ticker} ({interval})",
        fontsize=14,
        pad=20,
    )
    plt.xlabel("ATR Multiplier", fontsize=12, labelpad=10)
    plt.ylabel("ATR Length", fontsize=12, labelpad=10)

    # Adjust font sizes for better readability
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)

    plt.tight_layout()
    plt.show()


def main(config: ATRConfig | None = None) -> None:
    """
    Main function to run the ATR analysis.

    Args:
        config (ATRConfig, optional): Configuration dictionary. If None, DEFAULT_CONFIG is used.
    """
    # Use default config if none provided
    if config is None:
        config = DEFAULT_CONFIG

    try:
        log("Starting ATR analysis")

        # Set up time period based on config
        end_date: datetime = datetime.now()
        years: int = 2 if config["USE_HOURLY"] else 10
        start_date: datetime = end_date - timedelta(days=365 * years)
        interval: str = "1h" if config["USE_HOURLY"] else "1d"

        log(f"Analysis period: {start_date} to {end_date} ({years} years)")

        # Define parameter ranges for testing
        atr_lengths: List[int] = list(range(2, 15))
        atr_multipliers: List[float] = list(np.arange(1.5, 8.5, 0.5))
        log(
            f"Testing {len(atr_lengths)} ATR lengths and {len(atr_multipliers)} ATR multipliers"
        )

        # Get data based on configuration
        if config["USE_SYNTHETIC"]:
            log(
                f"Using synthetic ticker with {config['TICKER_1']} and {config['TICKER_2']}"
            )

            # Create data configs for both tickers
            data_config_1: DataConfig = {
                "TICKER": config["TICKER_1"],
                "USE_HOURLY": config["USE_HOURLY"],
                "USE_YEARS": True,
                "YEARS": years,
                "BASE_DIR": ".",
            }

            data_config_2: DataConfig = {
                "TICKER": config["TICKER_2"],
                "USE_HOURLY": config["USE_HOURLY"],
                "USE_YEARS": True,
                "YEARS": years,
                "BASE_DIR": ".",
            }

            # Download data for both tickers in parallel
            log("DEBUG: Downloading data using centralized download_data function")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future1 = executor.submit(
                    download_data, config["TICKER_1"], data_config_1, log
                )
                future2 = executor.submit(
                    download_data, config["TICKER_2"], data_config_2, log
                )
                polars_data_1 = future1.result()
                polars_data_2 = future2.result()

            # Convert to pandas for processing
            log("DEBUG: Converting Polars DataFrames to Pandas")
            data_ticker_1 = polars_data_1.to_pandas()
            data_ticker_2 = polars_data_2.to_pandas()

            # Set Date as index
            log("DEBUG: Setting Date as index for synthetic data processing")
            data_ticker_1 = data_ticker_1.set_index("Date")
            data_ticker_2 = data_ticker_2.set_index("Date")

            # Process synthetic data with vectorized operations
            log("Processing synthetic data")
            data_ticker_1["Close"] = data_ticker_1["Close"].fillna(method="ffill")
            data_ticker_2["Close"] = data_ticker_2["Close"].fillna(method="ffill")

            # Create synthetic data with vectorized operations
            data = pd.DataFrame(index=data_ticker_1.index)
            for col in ["Close", "Open", "High", "Low"]:
                log(f"DEBUG: Creating synthetic {col} column")
                data[col] = data_ticker_1[col] / data_ticker_2[col]

            data["Volume"] = (data_ticker_1["Volume"] + data_ticker_2["Volume"]) / 2
            data = data.dropna()

            # Create synthetic ticker name
            base_currency: str = config["TICKER_1"][:3]
            quote_currency: str = config["TICKER_2"][:3]
            ticker: str = f"{base_currency}/{quote_currency}"
            log(f"Created synthetic ticker: {ticker} with {len(data)} data points")

            # Debug column structure
            log(f"DEBUG: Synthetic data columns: {data.columns.tolist()}")
            log(f"DEBUG: Synthetic data shape: {data.shape}")
            for col in data.columns:
                log(
                    f"DEBUG: Column {col} type: {type(data[col])}, shape: {data[col].shape}"
                )
        else:
            log(f"Using single ticker: {config['TICKER_1']}")

            # Create data config
            data_config: DataConfig = {
                "TICKER": config["TICKER_1"],
                "USE_HOURLY": config["USE_HOURLY"],
                "USE_YEARS": True,
                "YEARS": years,
                "BASE_DIR": ".",
            }

            # Download data using the centralized function
            log("DEBUG: Calling centralized download_data function")
            polars_data = download_data(config["TICKER_1"], data_config, log)

            # Convert to pandas and set index
            log("DEBUG: Converting Polars DataFrame to Pandas")
            data = polars_data.to_pandas()

            log(
                f"DEBUG: Pandas DataFrame columns before setting index: {data.columns.tolist()}"
            )
            log(f"DEBUG: Pandas DataFrame shape before setting index: {data.shape}")

            data = data.set_index("Date")

            log(
                f"DEBUG: Pandas DataFrame columns after setting index: {data.columns.tolist()}"
            )
            log(f"DEBUG: Pandas DataFrame shape after setting index: {data.shape}")

            ticker = config["TICKER_1"]
            log(f"Downloaded {len(data)} data points for {ticker}")

            # Debug column structure
            for col in data.columns:
                log(
                    f"DEBUG: Column {col} type: {type(data[col])}, shape: {data[col].shape}"
                )

        # Run parameter sensitivity analysis
        log("Starting parameter sensitivity analysis")
        results = parameter_sensitivity_analysis(data, atr_lengths, atr_multipliers)
        log(f"Completed parameter sensitivity analysis, results shape: {results.shape}")

        # Check if results contain any valid values
        if results.notna().any().any():
            # Find best parameters
            best_params = results.stack().idxmax()
            best_return = results.stack().max()

            # Log and print results
            log(
                f"Best parameters: ATR Length: {best_params[0]}, ATR Multiplier: {best_params[1]}, Return: {best_return:.3f}"
            )
            print(
                f"Best parameters for {interval} {ticker}: ATR Length: {best_params[0]}, ATR Multiplier: {best_params[1]}"
            )
            print(f"Best total return: {best_return:.3f}")

            # Generate visualization
            log("Generating heatmap")
            plot_heatmap(results, ticker, config)
        else:
            log("No valid results found. All parameter combinations failed.", "warning")
            print("No valid results found. All parameter combinations failed.")
            best_params = None
            best_return = None

        log("Analysis complete")
        log_close()  # Close logging and print execution time

        return results, best_params, best_return
    except Exception as e:
        log(f"Error in main function: {str(e)}", "error")
        raise


if __name__ == "__main__":
    main(DEFAULT_CONFIG)

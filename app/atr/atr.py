from typing import Tuple, List
import yfinance as yf
import pandas as pd
import numpy as np
import vectorbt as vbt
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from functools import lru_cache
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants for easy configuration
USE_HOURLY: bool = False  # Set to False for daily data
USE_SYNTHETIC: bool = False  # Toggle between synthetic and original ticker
TICKER_1: str = 'BTC-USD'  # Ticker for X to USD
TICKER_2: str = 'BTC-USD'  # Ticker for Y to USD

interval: str = '1h' if USE_HOURLY else '1d'

logger.info(f"Starting ATR analysis with ticker: {TICKER_1}, interval: {interval}")

@lru_cache(maxsize=None)
def download_data(ticker: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Download historical data from Yahoo Finance."""
    logger.info(f"Downloading data for {ticker} from {start_date} to {end_date} with interval {interval}")
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    logger.info(f"Downloaded {len(data)} rows of data for {ticker}")
    return data

def calculate_atr(data: pd.DataFrame, length: int) -> pd.Series:
    """Calculate Average True Range (ATR)."""
    high_low: pd.Series = data['High'] - data['Low']
    high_close: pd.Series = np.abs(data['High'] - data['Close'].shift())
    low_close: pd.Series = np.abs(data['Low'] - data['Close'].shift())
    ranges: pd.DataFrame = pd.concat([high_low, high_close, low_close], axis=1)
    true_range: pd.Series = np.max(ranges, axis=1)
    return true_range.rolling(window=length).mean()

def calculate_atr_trailing_stop(close: float, atr: float, multiplier: float, highest_since_entry: float, previous_stop: float) -> float:
    """Calculate ATR Trailing Stop."""
    potential_stop: float = close - (atr * multiplier)
    if np.isnan(previous_stop):
        return potential_stop
    new_stop: float = highest_since_entry - (atr * multiplier)
    return max(new_stop, previous_stop)
def generate_signals(data: pd.DataFrame, atr_length: int, atr_multiplier: float) -> pd.DataFrame:
    """
    Generate trading signals based on ATR Trailing Stop.
    
    Args:
        data (pd.DataFrame): Price data
        atr_length (int): ATR length
        atr_multiplier (float): ATR multiplier
        
    Returns:
        pd.DataFrame: Data with signals
    """
    logger.info(f"Generating signals with ATR length: {atr_length}, multiplier: {atr_multiplier}")
    
    # Create a copy to avoid modifying the original
    data = data.copy()
    
    # Calculate ATR
    data['ATR'] = calculate_atr(data, atr_length)
    data['Signal'] = 0
    data['ATR_Trailing_Stop'] = np.nan
    data['Highest_Since_Entry'] = np.nan

    in_position: bool = False
    entry_price: float = 0
    
    logger.info(f"Data shape: {data.shape}, columns: {data.columns.tolist()}")

    # Helper function to safely get a scalar value
    def get_scalar(value):
        if isinstance(value, pd.Series):
            logger.debug(f"Converting Series to scalar: {value}")
            if len(value) == 1:
                return value.item()
            else:
                # Handle unexpected case
                logger.warning(f"Unexpected Series length: {len(value)}, using first value")
                return float(value.iloc[0])
        return value

    for i in range(1, len(data)):
        # Get scalar values for current row
        current_close = get_scalar(data['Close'].iloc[i])
        current_atr = get_scalar(data['ATR'].iloc[i])
        
        # Check for entry condition
        potential_stop = calculate_atr_trailing_stop(
            current_close,
            current_atr,
            atr_multiplier,
            current_close,
            np.nan
        )
        
        # Safe comparison
        price_above_stop = current_close >= potential_stop
        
        if price_above_stop and not in_position:
            data.loc[data.index[i], 'Signal'] = 1
            data.loc[data.index[i], 'ATR_Trailing_Stop'] = potential_stop
            data.loc[data.index[i], 'Highest_Since_Entry'] = current_close
            in_position = True
            entry_price = current_close
        elif in_position:
            # Update highest price since entry
            prev_highest = get_scalar(data['Highest_Since_Entry'].iloc[i-1])
            highest_since_entry = max(prev_highest, current_close)
            data.loc[data.index[i], 'Highest_Since_Entry'] = highest_since_entry
            
            # Get previous stop as scalar
            prev_stop = get_scalar(data['ATR_Trailing_Stop'].iloc[i-1])
            
            # Calculate new trailing stop
            new_stop = calculate_atr_trailing_stop(
                current_close,
                current_atr,
                atr_multiplier,
                highest_since_entry,
                prev_stop
            )
            data.loc[data.index[i], 'ATR_Trailing_Stop'] = new_stop

            # Safe comparison
            if current_close < new_stop:
                data.loc[data.index[i], 'Signal'] = 0
                in_position = False
            else:
                data.loc[data.index[i], 'Signal'] = 1

    data['Position'] = data['Signal'].shift()
    return data

def backtest_strategy(data: pd.DataFrame) -> vbt.Portfolio:
    """Backtest the ATR Trailing Stop."""
    portfolio: vbt.Portfolio = vbt.Portfolio.from_signals(
        close=data['Close'],
        entries=(data['Signal'] == 1) & (data['Signal'].shift() != 1),
        exits=(data['Signal'] == 0) & (data['Signal'].shift() == 1),
        init_cash=1000,
        fees=0.001
    )
    return portfolio

def analyze_params(data: pd.DataFrame, atr_length: int, atr_multiplier: float) -> Tuple[int, float, float]:
    """
    Analyze parameters for ATR trailing stop strategy.
    
    Args:
        data (pd.DataFrame): Price data
        atr_length (int): ATR length
        atr_multiplier (float): ATR multiplier
        
    Returns:
        Tuple[int, float, float]: ATR length, ATR multiplier, total return
    """
    logger.info(f"Analyzing parameters: ATR length={atr_length}, multiplier={atr_multiplier}")
    
    try:
        data_with_signals: pd.DataFrame = generate_signals(data.copy(), atr_length, atr_multiplier)
        logger.info(f"Generated signals successfully, data shape: {data_with_signals.shape}")
        
        portfolio: vbt.Portfolio = backtest_strategy(data_with_signals)
        logger.info(f"Backtested strategy successfully")
        
        # Ensure total_return is a scalar value
        total_return_value = portfolio.total_return()
        logger.info(f"Total return type: {type(total_return_value)}, value: {total_return_value}")
        
        if isinstance(total_return_value, pd.Series):
            logger.info(f"Converting Series to scalar, Series shape: {total_return_value.shape}")
            if len(total_return_value) == 1:
                total_return_value = total_return_value.item()
                logger.info(f"Converted to scalar using item(): {total_return_value}")
            else:
                logger.warning(f"Unexpected Series length: {len(total_return_value)}, using first value")
                total_return_value = float(total_return_value.iloc[0])
                logger.info(f"Converted to scalar using iloc[0]: {total_return_value}")
        
        return atr_length, atr_multiplier, total_return_value
    except Exception as e:
        logger.error(f"Error in analyze_params: {str(e)}", exc_info=True)
        raise
def parameter_sensitivity_analysis(data: pd.DataFrame, atr_lengths: List[int], atr_multipliers: List[float]) -> pd.DataFrame:
    """
    Perform parameter sensitivity analysis without using ProcessPoolExecutor to avoid serialization issues.
    
    Args:
        data (pd.DataFrame): Price data
        atr_lengths (List[int]): List of ATR lengths to test
        atr_multipliers (List[float]): List of ATR multipliers to test
        
    Returns:
        pd.DataFrame: Results matrix with ATR lengths as index and ATR multipliers as columns
    """
    logger.info(f"Starting parameter sensitivity analysis with {len(atr_lengths)} lengths and {len(atr_multipliers)} multipliers")
    logger.info(f"ATR lengths: {atr_lengths}")
    logger.info(f"ATR multipliers: {atr_multipliers}")
    
    try:
        # Initialize results as a dictionary for safer assignment
        results_dict = {}
        
        # Use a simple for loop instead of ProcessPoolExecutor
        total_combinations = len(atr_lengths) * len(atr_multipliers)
        current_combination = 0
        
        for length in atr_lengths:
            for multiplier in atr_multipliers:
                current_combination += 1
                logger.info(f"Processing combination {current_combination}/{total_combinations}: length={length}, multiplier={multiplier}")
                
                try:
                    length_val, multiplier_val, total_return = analyze_params(data, length, multiplier)
                    logger.info(f"Result for length={length}, multiplier={multiplier}: total_return={total_return}")
                    
                    # Store results in a dictionary with tuple keys
                    if length not in results_dict:
                        results_dict[length] = {}
                    results_dict[length][multiplier] = total_return
                except Exception as e:
                    logger.error(f"Error analyzing params for length={length}, multiplier={multiplier}: {str(e)}")
                    # Continue with other combinations even if one fails
                    continue
        
        logger.info(f"Completed all parameter combinations. Converting results to DataFrame.")
        
        # Convert dictionary to DataFrame
        logger.info(f"Converting results dictionary to DataFrame, keys: {list(results_dict.keys())}")
        
        # Create an empty DataFrame with the correct index and columns
        results = pd.DataFrame(index=atr_lengths, columns=atr_multipliers)
        results.index.name = 'ATR Length'
        results.columns.name = 'ATR Multiplier'
        
        # Fill in the values from our dictionary
        for length in results_dict:
            for multiplier in results_dict[length]:
                results.loc[length, multiplier] = results_dict[length][multiplier]
        
        logger.info(f"Results DataFrame shape: {results.shape}")
        return results
    except Exception as e:
        logger.error(f"Error in parameter_sensitivity_analysis: {str(e)}", exc_info=True)
        raise

def plot_heatmap(results: pd.DataFrame, ticker: str) -> None:
    """Plot heatmap of the results."""
    plt.figure(figsize=(12, 8))
    sns.heatmap(results.astype(float), annot=True, cmap="YlGnBu", fmt='.3f', cbar_kws={'label': 'Total Return'})
    timeframe: str = "Hourly" if USE_HOURLY else "Daily"
    plt.title(f'Parameter Sensitivity Analysis - ATR Trailing Stop ({timeframe}) for {ticker}')
    plt.xlabel('ATR Multiplier')
    plt.ylabel('ATR Length')
    plt.tight_layout()
    plt.show()

def main() -> None:
    """Main function to run the ATR analysis."""
    try:
        logger.info("Starting ATR analysis")
        
        end_date: datetime = datetime.now()
        years: int = 2 if USE_HOURLY else 10
        start_date: datetime = end_date - timedelta(days=365 * years)
        logger.info(f"Analysis period: {start_date} to {end_date} ({years} years)")

        # atr_lengths: List[int] = list(range(2, 15))
        # atr_multipliers: List[float] = list(np.arange(2.5, 12.5, 0.5))
        atr_lengths: List[int] = list(range(2, 8))
        atr_multipliers: List[float] = list(np.arange(2.5, 6, 0.5))
        logger.info(f"Testing {len(atr_lengths)} ATR lengths and {len(atr_multipliers)} ATR multipliers")

        if USE_SYNTHETIC:
            logger.info(f"Using synthetic ticker with {TICKER_1} and {TICKER_2}")
            data_ticker_1: pd.DataFrame = download_data(TICKER_1, start_date, end_date)
            data_ticker_2: pd.DataFrame = download_data(TICKER_2, start_date, end_date)
            
            logger.info("Processing synthetic data")
            data_ticker_1['Close'] = data_ticker_1['Close'].fillna(method='ffill')
            data_ticker_2['Close'] = data_ticker_2['Close'].fillna(method='ffill')
            data: pd.DataFrame = pd.DataFrame(index=data_ticker_1.index)
            data['Close'] = data_ticker_1['Close'] / data_ticker_2['Close']
            data['Open'] = data_ticker_1['Open'] / data_ticker_2['Open']
            data['High'] = data_ticker_1['High'] / data_ticker_2['High']
            data['Low'] = data_ticker_1['Low'] / data_ticker_2['Low']
            data['Volume'] = (data_ticker_1['Volume'] + data_ticker_2['Volume']) / 2
            data = data.dropna()
            
            base_currency: str = TICKER_1[:3]
            quote_currency: str = TICKER_2[:3]
            synthetic_ticker: str = f"{base_currency}/{quote_currency}"
            logger.info(f"Created synthetic ticker: {synthetic_ticker} with {len(data)} data points")
        else:
            logger.info(f"Using single ticker: {TICKER_1}")
            data: pd.DataFrame = download_data(TICKER_1, start_date, end_date)
            synthetic_ticker: str = TICKER_1
            logger.info(f"Downloaded {len(data)} data points for {TICKER_1}")

        logger.info("Starting parameter sensitivity analysis")
        results: pd.DataFrame = parameter_sensitivity_analysis(data, atr_lengths, atr_multipliers)
        logger.info(f"Completed parameter sensitivity analysis, results shape: {results.shape}")
        
        best_params: Tuple[int, float] = results.stack().idxmax()
        best_return: float = results.stack().max()
        logger.info(f"Best parameters: ATR Length: {best_params[0]}, ATR Multiplier: {best_params[1]}, Return: {best_return:.3f}")
        print(f"Best parameters for {interval} {synthetic_ticker}: ATR Length: {best_params[0]}, ATR Multiplier: {best_params[1]}")
        print(f"Best total return: {best_return:.3f}")
        
        logger.info("Generating heatmap")
        plot_heatmap(results, synthetic_ticker)
        logger.info("Analysis complete")
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
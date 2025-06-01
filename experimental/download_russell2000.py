import os
import time
from typing import List, Dict, Set
import yfinance as yf
import polars as pl
import pandas as pd
from datetime import datetime

from app.tools.setup_logging import setup_logging

def load_progress(file_path: str) -> Set[str]:
    """
    Load previously downloaded tickers from CSV file.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        Set[str]: Set of tickers that have already been downloaded
    """
    if os.path.exists(file_path):
        try:
            df = pl.read_csv(file_path)
            return set(df['Ticker'].unique().to_list())
        except:
            return set()
    return set()

def download_ticker_data(ticker: str, log: callable) -> pd.DataFrame:
    """
    Download data for a single ticker with retries.
    
    Args:
        ticker (str): Ticker symbol
        log (callable): Logging function
        
    Returns:
        pd.DataFrame: Price data or empty DataFrame if download fails
    """
    max_retries = 3
    retry_delay = 5
    
    for retry in range(max_retries):
        try:
            if retry > 0:
                log(f"Retry {retry + 1} for {ticker}")
                time.sleep(retry_delay)
                
            # Use yfinance Ticker object
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(
                start="2010-01-01",
                end=datetime.now().strftime("%Y-%m-%d"),
                auto_adjust=True
            )
            
            if data.empty:
                log(f"No data available for {ticker}")
                return pd.DataFrame()
                
            # Process the data
            data = data.reset_index()
            data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
            data['Ticker'] = ticker
            
            # Select and rename columns
            result = pd.DataFrame({
                'Date': data['Date'],
                'Ticker': data['Ticker'],
                'Open': data['Open'],
                'High': data['High'],
                'Low': data['Low'],
                'Close': data['Close'],
                'Volume': data['Volume'].fillna(0)
            })
            
            return result
            
        except Exception as e:
            if retry == max_retries - 1:
                log(f"Failed to download {ticker}: {str(e)}")
                return pd.DataFrame()
                
    return pd.DataFrame()

def save_data(data: pd.DataFrame, output_file: str, log: callable) -> bool:
    """
    Save data to CSV file with error handling.
    
    Args:
        data (pd.DataFrame): Data to save
        output_file (str): Output file path
        log (callable): Logging function
        
    Returns:
        bool: True if save successful, False otherwise
    """
    try:
        # Convert to Polars with explicit schema
        pl_data = pl.DataFrame({
            'Date': pl.Series(data['Date']),
            'Ticker': pl.Series(data['Ticker']),
            'Open': pl.Series(data['Open'], dtype=pl.Float64),
            'High': pl.Series(data['High'], dtype=pl.Float64),
            'Low': pl.Series(data['Low'], dtype=pl.Float64),
            'Close': pl.Series(data['Close'], dtype=pl.Float64),
            'Volume': pl.Series(data['Volume'], dtype=pl.Float64)
        })
        
        if os.path.exists(output_file):
            existing_data = pl.read_csv(output_file)
            combined_data = pl.concat([existing_data, pl_data])
            combined_data.write_csv(output_file)
        else:
            pl_data.write_csv(output_file)
            
        return True
        
    except Exception as e:
        log(f"Error saving data: {str(e)}")
        return False

def download_price_histories(tickers: List[str], log: callable) -> None:
    """
    Download full price history for given tickers and save to CSV.

    Args:
        tickers (List[str]): List of ticker symbols
        log (callable): Logging function
    
    Raises:
        Exception: If price download fails
    """
    try:
        # Create data directory if it doesn't exist
        data_dir = os.path.join("csv", "experimental", "russell2000")
        os.makedirs(data_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_file = os.path.join(data_dir, f"russell2000_prices_{timestamp}.csv")
        
        # Load progress if file exists
        completed_tickers = load_progress(output_file)
        remaining_tickers = [t for t in tickers if t not in completed_tickers]
        
        if completed_tickers:
            log(f"Resuming download - {len(completed_tickers)} tickers already downloaded")
        
        successful_count = len(completed_tickers)
        failed_count = 0
        
        for i, ticker in enumerate(remaining_tickers, 1):
            try:
                log(f"Processing ticker {i} of {len(remaining_tickers)} ({ticker})")
                
                # Download data for this ticker
                data = download_ticker_data(ticker, log)
                
                if not data.empty:
                    if save_data(data, output_file, log):
                        successful_count += 1
                        log(f"Successfully downloaded {ticker}")
                    else:
                        failed_count += 1
                        log(f"Failed to save data for {ticker}")
                else:
                    failed_count += 1
                
                # Add delay between tickers
                time.sleep(2)
                
                # Log progress every 10 tickers
                if i % 10 == 0:
                    log(f"Progress update - Successful: {successful_count}, Failed: {failed_count}")
                    
            except Exception as e:
                log(f"Error processing {ticker}: {str(e)}")
                failed_count += 1
                continue
        
        if successful_count == 0:
            raise Exception("No data was downloaded")
        
        log(f"Download complete - Successfully downloaded {successful_count} tickers, Failed: {failed_count}")
        log(f"Price histories saved to {output_file}")
            
    except Exception as e:
        raise Exception(f"Error downloading price histories: {str(e)}")

def get_russell2000_tickers(log: callable) -> List[str]:
    """
    Get list of Russell 2000 constituents from iShares IWM ETF holdings.

    Args:
        log (callable): Logging function

    Returns:
        List[str]: List of ticker symbols
    
    Raises:
        Exception: If unable to fetch Russell 2000 constituents
    """
    try:
        # iShares IWM ETF holdings URL
        url = "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf/1467271812596.ajax?fileType=csv&fileName=IWM_holdings&dataType=fund"
        
        # Read CSV directly into Polars
        holdings = pd.read_csv(url, skiprows=9)
        holdings_pl = pl.from_pandas(holdings)
        
        # Debug log the columns we have
        log(f"Available columns: {holdings_pl.columns}")
        
        # The column name might be different, let's find it
        ticker_column = None
        possible_names = ["Ticker", "Symbol", "ticker", "symbol"]
        for name in possible_names:
            if name in holdings_pl.columns:
                ticker_column = name
                break
                
        if ticker_column is None:
            raise Exception(f"Could not find ticker column in available columns: {holdings_pl.columns}")
            
        log(f"Using column: {ticker_column}")
        
        # Extract ticker symbols
        tickers = holdings_pl.select(ticker_column).to_series().to_list()
        log(f"Found {len(tickers)} raw tickers")
        
        # Clean and filter tickers
        clean_tickers = []
        for ticker in tickers:
            if isinstance(ticker, str) and ticker.strip():
                # Remove any whitespace and take first part if there's a space
                clean_ticker = ticker.strip()
                if ' ' in clean_ticker:
                    clean_ticker = clean_ticker.split()[0]
                if clean_ticker:
                    clean_tickers.append(clean_ticker)
        
        if not clean_tickers:
            raise Exception("No valid tickers found in holdings data")
            
        log(f"Extracted {len(clean_tickers)} clean tickers")
        return clean_tickers
        
    except Exception as e:
        raise Exception(f"Error getting Russell 2000 tickers: {str(e)}")

def main() -> None:
    """Main execution function."""
    log, log_close, _, _ = setup_logging(
        "experimental",
        "russell2000_download.log",
        log_subdir="russell2000"
    )
    
    try:
        log("Starting Russell 2000 data download")
        
        # Get Russell 2000 tickers
        log("Fetching Russell 2000 constituents")
        tickers = get_russell2000_tickers(log)
        log(f"Found {len(tickers)} tickers")
        
        # Download price histories
        log("Downloading price histories")
        download_price_histories(tickers, log)
        
        log("Download completed successfully")
        log_close()
        
    except Exception as e:
        log(f"Error: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    main()
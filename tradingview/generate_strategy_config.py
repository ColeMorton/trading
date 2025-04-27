#!/usr/bin/env python3
"""
Strategy Configuration Generator for TradingView Pine

This script reads the strategy parameters from a CSV file and generates
the Pine script configuration code that can be used to update the
Strategy Breadth Oscillator indicator.
"""

import csv
import os
import sys
from datetime import datetime
from collections import defaultdict

def generate_pine_config(csv_path, ticker_filter=None):
    """
    Generate Pine script configuration from CSV file.
    
    Args:
        csv_path: Path to the CSV file containing strategy parameters
        ticker_filter: Optional ticker symbol to filter strategies (e.g., 'BTC-USD')
        
    Returns:
        A tuple containing:
        - The Pine script configuration code
        - The number of strategies found
        - The date from the CSV filename (if available)
        - A list of unique tickers found
        - The ticker input code
    """
    strategies = []
    tickers = set()
    ticker_strategy_counts = defaultdict(int)
    
    # Extract date from filename if possible
    filename = os.path.basename(csv_path)
    date_str = ""
    if "_" in filename and filename.endswith(".csv"):
        parts = filename.split("_")
        if len(parts) > 1:
            date_part = parts[-1].replace(".csv", "")
            if date_part.isdigit() and len(date_part) == 8:  # YYYYMMDD format
                date_str = date_part
    
    # Read strategies from CSV
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ticker = row.get('Ticker', 'ALL')
            tickers.add(ticker)
            
            # Skip if ticker filter is provided and doesn't match
            if ticker_filter and ticker != ticker_filter:
                continue
                
            strategy_type = row.get('Strategy Type', '')
            short_window = row.get('Short Window', '')
            long_window = row.get('Long Window', '')
            signal_window = row.get('Signal Window', '0')
            
            # Skip rows with missing data
            if not all([strategy_type, short_window, long_window]):
                continue
                
            # Create strategy configuration string
            strategy_config = f'array.push(strategy_configs, "{ticker},{strategy_type},{short_window},{long_window},{signal_window}")'
            strategies.append(strategy_config)
            ticker_strategy_counts[ticker] += 1
    
    # Generate the Pine script code
    pine_code = [
        "// Strategy configuration array - Auto-generated from CSV",
        f"// Source: {csv_path}",
        f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    
    # Add ticker information
    if ticker_filter:
        pine_code.append(f"// Filtered for ticker: {ticker_filter}")
        pine_code.append(f"// Total strategies for {ticker_filter}: {len(strategies)}")
    else:
        pine_code.append(f"// Total strategies: {len(strategies)}")
        for ticker, count in ticker_strategy_counts.items():
            pine_code.append(f"// Strategies for {ticker}: {count}")
    
    pine_code.extend([
        "",
        "var strategy_configs = array.new_string(0)",
        ""
    ])
    
    # Add each strategy configuration
    pine_code.extend(strategies)
    
    # Generate ticker options for input
    ticker_options = sorted(list(tickers))
    if len(ticker_options) > 1 and 'ALL' not in ticker_options:
        ticker_options.insert(0, 'ALL')
    
    ticker_input_code = [
        "",
        "// Ticker selection for filtering strategies",
        f'tickerInput = input.string("{ticker_options[0]}", "Ticker for Strategies", options={str(ticker_options)})'
    ]
    
    return "\n".join(pine_code), len(strategies), date_str, ticker_options, "\n".join(ticker_input_code)

def generate_dynamic_calculation_function():
    """
    Generate the dynamic calculation function for processing strategies.
    
    Returns:
        The Pine script code for the dynamic calculation function
    """
    code = """
// Dynamic strategy calculation function
calculateBreadth() =>
    int strategiesInPosition = 0
    int totalApplicableStrategies = 0
    
    // Process each strategy from the configuration
    int size = array.size(strategy_configs)
    for i = 0 to size - 1
        string config = array.get(strategy_configs, i)
        string[] params = str.split(config, ",")
        
        // Extract ticker and parameters
        string ticker = array.get(params, 0)
        
        // Skip if not matching the current ticker and not set to "ALL"
        if ticker != tickerInput and ticker != "ALL" and tickerInput != "ALL"
            continue
            
        totalApplicableStrategies += 1
        string type = array.get(params, 1)
        int shortWindow = int(str.tonumber(array.get(params, 2)))
        int longWindow = int(str.tonumber(array.get(params, 3)))
        int signalWindow = int(str.tonumber(array.get(params, 4)))
        
        // Check parameters
        shortWindow := checkParameter(shortWindow, "Short Window")
        longWindow := checkParameter(longWindow, "Long Window")
        signalWindow := checkParameter(signalWindow, "Signal Window")
        
        // Process based on strategy type
        bool isActive = false
        if type == "SMA"
            isActive := smaCrossSignal(shortWindow, longWindow)
        else if type == "EMA"
            isActive := emaCrossSignal(shortWindow, longWindow)
        else if type == "MACD"
            isActive := macdSignal(shortWindow, longWindow, signalWindow)
            
        if isActive
            strategiesInPosition += 1
    
    // Return both the active strategies and the total applicable strategies
    [strategiesInPosition, totalApplicableStrategies]
"""
    return code

def main():
    """Main function to run the generator."""
    if len(sys.argv) < 2:
        print("Usage: python generate_strategy_config.py <path_to_csv_file> [ticker_filter]")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    ticker_filter = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    
    # Generate the configuration
    config_code, strategy_count, date_str, tickers, ticker_input_code = generate_pine_config(csv_path, ticker_filter)
    
    # Generate the calculation function
    calc_function = generate_dynamic_calculation_function()
    
    # Output to console
    print(config_code)
    print("\n// ================ Ticker Selection ================")
    print(ticker_input_code)
    print("\n// ================ Dynamic Calculation Function ================")
    print(calc_function)
    
    # Determine output filename
    ticker_part = f"_{ticker_filter}" if ticker_filter else ""
    output_file = f"strategy_config{ticker_part}_{date_str or 'generated'}.pine"
    
    # Save to file
    with open(output_file, 'w') as f:
        f.write(config_code)
        f.write("\n\n// ================ Ticker Selection ================\n")
        f.write(ticker_input_code)
        f.write("\n\n// ================ Dynamic Calculation Function ================\n")
        f.write(calc_function)
    
    print(f"\nConfiguration saved to {output_file}")
    print(f"Total strategies: {strategy_count}")
    print(f"Available tickers: {', '.join(tickers)}")
    print(f"Note: The totalStrategies variable is now dynamically updated based on applicable strategies for the selected ticker")

if __name__ == "__main__":
    main()
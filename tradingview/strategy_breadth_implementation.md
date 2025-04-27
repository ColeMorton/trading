# Strategy Breadth Oscillator Implementation

This document provides a comprehensive guide to the refactored Strategy Breadth Oscillator implementation, including how to use and maintain it.

## Overview

The Strategy Breadth Oscillator tracks multiple trading strategies and displays how many are in bullish positions at any given time. The refactored implementation makes it easier to update when the source CSV file changes and adds support for strategies across different assets.

## Files

- `generate_strategy_config.py`: Python script that generates the Pine script configuration from the CSV file
- `update_strategy_breadth.py`: Python script that automatically updates the Pine script with the generated configuration
- `update_strategy_breadth.sh`: Shell script that provides a user-friendly interface for the update process
- `test_strategy_generator.py`: Test script that demonstrates how to use the generator with different CSV files
- `strategy_breadth_refactored.pine`: Refactored Pine script with dynamic strategy processing and ticker support
- `strategy_breadth_refactored_README.md`: User guide for the refactored implementation

## Implementation Details

### 1. Strategy Configuration Generator

The `generate_strategy_config.py` script reads the strategy parameters from a CSV file and generates the Pine script configuration. It supports filtering by ticker and automatically generates the ticker selection input.

Key features:
- Extracts strategy parameters from the CSV file
- Supports filtering by ticker
- Generates the strategy configuration array
- Generates the ticker selection input
- Generates the dynamic calculation function

### 2. Automatic Updater

The `update_strategy_breadth.py` script automates the process of updating the Pine script with the generated configuration. It extracts the relevant sections from the generated configuration file and integrates them into the Pine script.

Key features:
- Creates a backup of the original Pine script
- Extracts sections from the generated configuration
- Updates the Pine script with the extracted sections
- Preserves the rest of the Pine script

### 3. User-Friendly Shell Script

The `update_strategy_breadth.sh` script provides a user-friendly interface for the update process. It accepts command-line arguments for the CSV file, Pine script, and ticker filter.

Key features:
- Accepts command-line arguments
- Validates input files
- Runs the update script
- Provides feedback on the update process

### 4. Refactored Pine Script

The `strategy_breadth_refactored.pine` script is the refactored implementation of the Strategy Breadth Oscillator. It uses a dynamic approach to process strategies based on their type and ticker.

Key features:
- Dynamic strategy processing
- Ticker support
- Automatic updating of the total strategies variable
- Visualization of the oscillator

## How to Use

### Initial Setup

1. Make sure you have Python installed on your system
2. Clone or download the repository
3. Navigate to the project directory

### Generating the Configuration

To generate the Pine script configuration from a CSV file:

```bash
python tradingview/generate_strategy_config.py csv/strategies/BTC_d_20250427.csv
```

This will generate a configuration file (e.g., `strategy_config_20250427.pine`) that contains the strategy configuration array, ticker selection input, and dynamic calculation function.

To filter for a specific ticker:

```bash
python tradingview/generate_strategy_config.py csv/strategies/BTC_d_20250427.csv BTC-USD
```

### Updating the Pine Script

To update the Pine script with the generated configuration:

```bash
python tradingview/update_strategy_breadth.py csv/strategies/BTC_d_20250427.csv tradingview/strategy_breadth_refactored.pine
```

Or use the shell script for a more user-friendly interface:

```bash
./tradingview/update_strategy_breadth.sh --csv csv/strategies/BTC_d_20250427.csv --pine tradingview/strategy_breadth_refactored.pine
```

### Testing the Generator

To test the generator with different CSV files:

```bash
python tradingview/test_strategy_generator.py
```

This will run the generator with different CSV files and ticker filters to demonstrate its capabilities.

### Using the Pine Script in TradingView

1. Upload the `strategy_breadth_refactored.pine` file to TradingView
2. Apply the indicator to a chart
3. Select the desired timeframe and ticker from the inputs
4. The indicator will display how many strategies are currently in bullish positions

## Maintenance Workflow

When the source CSV file changes (strategies are added/removed/improved), follow these steps to update the indicator:

1. Run the update script with the updated CSV file:
   ```bash
   ./tradingview/update_strategy_breadth.sh --csv path/to/updated/csv/file.csv
   ```

2. The script will automatically update the Pine script with the new configuration

3. Upload the updated Pine script to TradingView

## Adding New Strategy Types

The current implementation supports SMA, EMA, and MACD strategies. To add support for a new strategy type:

1. Add a new signal generation function in the Pine script:
   ```pine
   newStrategySignal(param1, param2) =>
       // Implementation
       result = ...
       result
   ```

2. Update the dynamic calculation function to handle the new strategy type:
   ```pine
   if type == "NEW_TYPE"
       isActive := newStrategySignal(param1, param2)
   ```

3. Add strategies of the new type to the CSV file

4. Run the update script to update the Pine script

## Multi-Asset Support

The refactored implementation supports strategies across different assets (tickers). The ticker selection input allows users to switch between different assets' strategies or view all strategies at once.

To generate a configuration for multiple assets:

1. Make sure the CSV file includes the Ticker column with different asset symbols
2. Run the generator script without a ticker filter to include all assets
3. The generated configuration will include all strategies for all assets
4. The ticker selection input will include all unique tickers from the CSV file

## Troubleshooting

If you encounter issues with the implementation:

1. Check that the CSV file has the correct format with the required columns (Ticker, Strategy Type, Short Window, Long Window, Signal Window)

2. Verify that the generated configuration includes all the expected strategies

3. Make sure the ticker selection input includes all the tickers from the CSV file

4. Check for any errors in the Pine script editor when uploading the updated script

5. If the update script fails, try running the generator script manually and copy the relevant sections to the Pine script

## Conclusion

The refactored Strategy Breadth Oscillator is now much easier to maintain and update. By using the provided scripts, you can quickly incorporate changes from the source CSV file without having to manually update the Pine script. The multi-asset support allows you to track strategies across different assets, providing a more comprehensive view of market sentiment.
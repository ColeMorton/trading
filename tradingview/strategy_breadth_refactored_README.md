# Strategy Breadth Oscillator - Refactored Implementation

This document provides instructions for using and maintaining the refactored Strategy Breadth Oscillator indicator.

## Overview

The Strategy Breadth Oscillator tracks multiple trading strategies and displays how many are in bullish positions at any given time. The refactored implementation makes it easier to update when the source CSV file changes and adds support for strategies across different assets.

## Files

- `generate_strategy_config.py`: Python script that generates the Pine script configuration from the CSV file
- `strategy_breadth_refactored.pine`: Refactored Pine script with dynamic strategy processing and ticker support

## How to Use

1. Upload the `strategy_breadth_refactored.pine` file to TradingView
2. Apply the indicator to a chart
3. Select the desired timeframe and ticker from the inputs
4. The indicator will display how many strategies are currently in bullish positions

## How to Update

When the source CSV file changes (strategies are added/removed/improved), follow these steps to update the indicator:

1. Run the Python generator script with the updated CSV file:
   ```bash
   python generate_strategy_config.py path/to/updated/csv/file.csv
   ```

2. The script will generate a new configuration file (e.g., `strategy_config_20250427.pine`)

3. Open the generated file and copy the following sections:
   - Strategy configuration array
   - Ticker selection input
   - Dynamic calculation function

4. Open `strategy_breadth_refactored.pine` and replace the corresponding sections with the copied content

5. Update the overboughtThreshold and oversoldThreshold input parameters if the number of strategies has changed significantly

6. Upload the updated Pine script to TradingView

## Filtering by Ticker

If you want to generate a configuration for a specific ticker only, you can specify the ticker when running the generator script:

```bash
python generate_strategy_config.py path/to/csv/file.csv BTC-USD
```

This will generate a configuration that only includes strategies for the specified ticker.

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

4. Run the generator script to update the configuration

## Troubleshooting

If you encounter issues with the indicator:

1. Check that the CSV file has the correct format with the required columns (Ticker, Strategy Type, Short Window, Long Window, Signal Window)

2. Verify that the generated configuration includes all the expected strategies

3. Make sure the ticker selection input includes all the tickers from the CSV file

4. Check for any errors in the Pine script editor when uploading the updated script

## Maintenance

To keep the indicator up to date:

1. Regularly check for updates to the source CSV file

2. Run the generator script whenever the CSV file changes

3. Keep a backup of the original Pine script in case you need to revert changes

4. Document any modifications you make to the Pine script or generator script

## Conclusion

The refactored Strategy Breadth Oscillator is now much easier to maintain and update. By using the Python generator script, you can quickly incorporate changes from the source CSV file without having to manually update the Pine script.
#!/bin/bash
# Update Strategy Breadth Pine Script
# This script demonstrates how to use the update_strategy_breadth.py script
# to update the Strategy Breadth Pine script when the CSV file changes.

# Set the default paths
CSV_FILE="csv/strategies/BTC_d_20250427.csv"
PINE_SCRIPT="tradingview/strategy_breadth_refactored.pine"
TICKER_FILTER=""

# Display usage information
function show_usage {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -c, --csv FILE       Path to the CSV file (default: $CSV_FILE)"
    echo "  -p, --pine FILE      Path to the Pine script (default: $PINE_SCRIPT)"
    echo "  -t, --ticker TICKER  Optional ticker filter"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --csv csv/strategies/DAILY.csv --pine tradingview/strategy_breadth_refactored.pine --ticker BTC-USD"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -c|--csv)
            CSV_FILE="$2"
            shift
            shift
            ;;
        -p|--pine)
            PINE_SCRIPT="$2"
            shift
            shift
            ;;
        -t|--ticker)
            TICKER_FILTER="$2"
            shift
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if the CSV file exists
if [ ! -f "$CSV_FILE" ]; then
    echo "Error: CSV file not found: $CSV_FILE"
    exit 1
fi

# Check if the Pine script exists
if [ ! -f "$PINE_SCRIPT" ]; then
    echo "Error: Pine script not found: $PINE_SCRIPT"
    exit 1
fi

# Run the update script
echo "Updating Strategy Breadth Pine script..."
echo "CSV file: $CSV_FILE"
echo "Pine script: $PINE_SCRIPT"
if [ -n "$TICKER_FILTER" ]; then
    echo "Ticker filter: $TICKER_FILTER"
    python tradingview/update_strategy_breadth.py "$CSV_FILE" "$PINE_SCRIPT" "$TICKER_FILTER"
else
    python tradingview/update_strategy_breadth.py "$CSV_FILE" "$PINE_SCRIPT"
fi

# Check if the update was successful
if [ $? -eq 0 ]; then
    echo "Update completed successfully!"
    echo "The Pine script has been updated with the latest strategy configuration."
    echo "You can now upload the updated Pine script to TradingView."
else
    echo "Update failed. Please check the error messages above."
fi
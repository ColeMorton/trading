#!/usr/bin/env python3
"""
Hardcoded Strategy Configuration Generator for TradingView Pine

This script reads the strategy parameters from a CSV file and generates
hardcoded strategy blocks for the Strategy Breadth Oscillator indicator,
following the best practices identified in the error resolution process.
"""

import csv
import os
import sys
from collections import defaultdict
from datetime import datetime


def generate_hardcoded_strategies(csv_path, ticker_filter=None):
    """
    Generate hardcoded strategy blocks from CSV file.

    Args:
        csv_path: Path to the CSV file containing strategy parameters
        ticker_filter: Optional ticker symbol to filter strategies

    Returns:
        A tuple containing:
        - A string containing hardcoded strategy blocks for the calculateBreadth() function
        - The number of strategies found
        - A list of unique tickers found
    """
    strategies = []
    tickers = set()
    ticker_strategy_counts = defaultdict(int)

    # Read strategies from CSV
    with open(csv_path) as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader):
            ticker = row.get("Ticker", "ALL")
            tickers.add(ticker)

            # Skip if ticker filter is provided and doesn't match
            if ticker_filter and ticker != ticker_filter:
                continue

            strategy_type = row.get("Strategy Type", "")
            fast_period = row.get("Fast Period", "")
            slow_period = row.get("Slow Period", "")
            signal_period = row.get("Signal Period", "0")

            # Skip rows with missing data
            if not all([strategy_type, fast_period, slow_period]):
                continue

            # Create hardcoded strategy block
            if strategy_type == "SMA":
                strategy_block = f"""
    // Strategy {i}: SMA({fast_period}, {slow_period})
    totalApplicableStrategies += 1
    if smaCrossSignal({fast_period}, {slow_period})
        strategiesInPosition += 1
"""
            elif strategy_type == "EMA":
                strategy_block = f"""
    // Strategy {i}: EMA({fast_period}, {slow_period})
    totalApplicableStrategies += 1
    if emaCrossSignal({fast_period}, {slow_period})
        strategiesInPosition += 1
"""
            elif strategy_type == "MACD":
                strategy_block = f"""
    // Strategy {i}: MACD({fast_period}, {slow_period}, {signal_period})
    totalApplicableStrategies += 1
    if macdSignal({fast_period}, {slow_period}, {signal_period})
        strategiesInPosition += 1
"""
            else:
                continue  # Skip unknown strategy types

            strategies.append(strategy_block)
            ticker_strategy_counts[ticker] += 1

    # Join all strategy blocks
    strategy_blocks = "".join(strategies)

    return strategy_blocks, len(strategies), tickers, ticker_strategy_counts


def generate_pine_script_from_template(
    csv_path, template_path=None, ticker_filter=None
):
    """
    Generate Pine script from template and CSV file.

    Args:
        csv_path: Path to the CSV file containing strategy parameters
        template_path: Optional path to the Pine script template
        ticker_filter: Optional ticker symbol to filter strategies

    Returns:
        A tuple containing:
        - The generated Pine script
        - The number of strategies found
    """
    # Generate hardcoded strategy blocks
    (
        strategy_blocks,
        strategy_count,
        tickers,
        ticker_strategy_counts,
    ) = generate_hardcoded_strategies(csv_path, ticker_filter)

    # Extract date from filename if possible
    filename = os.path.basename(csv_path)
    if "_" in filename and filename.endswith(".csv"):
        parts = filename.split("_")
        if len(parts) > 1:
            date_part = parts[-1].replace(".csv", "")
            if date_part.isdigit() and len(date_part) == 8:  # YYYYMMDD format
                pass

    # Generate ticker options for input
    ticker_options = sorted(tickers)
    if len(ticker_options) > 1 and "ALL" not in ticker_options:
        ticker_options.insert(0, "ALL")

    # Default template if none provided
    if not template_path:
        template = """
//@version=5
indicator("BTC Strategy Breadth Oscillator", shorttitle="StgyBreadth", overlay=false)

// Description:
// This indicator calculates how many strategies from a predefined collection
// are currently in a bullish position. It functions as a breadth oscillator that shows
// market sentiment based on multiple strategies simultaneously.

// ================ Main Configuration ================
var int totalStrategies = {{STRATEGY_COUNT}}  // Total number of strategies
var float lowerBand = 0.0     // Minimum oscillator value
var float upperBand = {{STRATEGY_COUNT}}.0    // Maximum oscillator value (total strategies)

// Default Colors
color bullColor = color.new(#26c6da, 0)
color bearColor = color.new(#7e57c2, 0)
color neutralColor = color.new(#3179f5, 0)

// Optional user inputs for time frame selection
timeframeInput = input.timeframe("D", "Strategy Timeframe", options=["H", "D", "W", "M"])

// Ticker selection for filtering strategies
tickerInput = input.string("{{DEFAULT_TICKER}}", "Ticker for Strategies", options={{TICKER_OPTIONS}})

// ================ Strategy Functions ================

// Function to calculate SMA Crossover signal
smaCrossSignal(shortWindow, longWindow) =>
    shortSMA = ta.sma(close, shortWindow)
    longSMA = ta.sma(close, longWindow)

    // Current state
    crossUp = shortSMA > longSMA

    // Return the signal (true if bullish)
    crossUp

// Function to calculate EMA Crossover signal
emaCrossSignal(shortWindow, longWindow) =>
    shortEMA = ta.ema(close, shortWindow)
    longEMA = ta.ema(close, longWindow)

    // Current state
    crossUp = shortEMA > longEMA

    // Return the signal (true if bullish)
    crossUp

// Function to calculate MACD signal
macdSignal(shortWindow, longWindow, signalWindow) =>
    [macdLine, signalLine, _] = ta.macd(close, shortWindow, longWindow, signalWindow)

    // Current state
    crossUp = macdLine > signalLine

    // Return the signal (true if bullish)
    crossUp

// ================ Error Handling Function ================
checkParameter(param, paramName) =>
    if param <= 0
        runtime.error("Invalid " + paramName + ": " + str.tostring(param) + ". Must be positive.")
        0
    else
        param

// ================ Strategy Configuration ================
// Strategy configuration - Hardcoded directly in calculateBreadth() function
// Source: {{CSV_PATH}}
// Generated: {{GENERATION_DATE}}
// Total strategies: {{STRATEGY_COUNT}}
{{TICKER_COUNTS}}

// ================ Dynamic Strategy Processing ================
calculateBreadth() =>
    int strategiesInPosition = 0
    int totalApplicableStrategies = 0

    // Process each strategy directly with hardcoded parameters
{{STRATEGY_BLOCKS}}

    // Return both the active strategies and the total applicable strategies
    [strategiesInPosition, totalApplicableStrategies]

// Request data using the specified timeframe
[strategiesActive, applicableStrategies] = request.security(syminfo.tickerid, timeframeInput, calculateBreadth())

// Update the total strategies variable based on applicable strategies
totalStrategies := applicableStrategies

// ================ Calculate Oscillator And Bands ================

// Calculate percentage of active strategies
strategyPercentage = (strategiesActive / totalStrategies) * 100

// Moving averages for signal lines
slowMA = ta.sma(strategiesActive, 20)
fastMA = ta.sma(strategiesActive, 5)

// Overbought/Oversold Thresholds
overboughtThreshold = input.int(8, "Overbought Threshold", minval=1, maxval={{STRATEGY_COUNT}})
oversoldThreshold = input.int(3, "Oversold Threshold", minval=0, maxval={{STRATEGY_COUNT_MINUS_1}})

// ================ Visualization ================

// Colors based on the position relative to thresholds
oscillatorColor = strategiesActive > overboughtThreshold ? bullColor :
                  strategiesActive < oversoldThreshold ? bearColor :
                  neutralColor

// Plotting the oscillator
plot(strategiesActive, "Active Strategies", color=oscillatorColor, linewidth=2)
plot(slowMA, "20-day SMA", color=color.new(#ffffff, 0), linewidth=1)

// Plot upper and lower reference lines - using dashed lines instead of style parameter
plot(overboughtThreshold, "Overbought", color=color.new(#26c6da, 40), linewidth=1)
plot(oversoldThreshold, "Oversold", color=color.new(#7e57c2, 40), linewidth=1)

// Plot range bands
hline(0, "Min", color=color.new(#717171, 70), linestyle=hline.style_dotted)
hline({{STRATEGY_COUNT}}, "Max", color=color.new(#717171, 70), linestyle=hline.style_dotted)

// ================ Alerts ================
// Create alerts for trading signals
crossingUp = ta.crossover(strategiesActive, oversoldThreshold)
crossingDown = ta.crossunder(strategiesActive, overboughtThreshold)
crossingMAUp = ta.crossover(fastMA, slowMA)
crossingMADown = ta.crossunder(fastMA, slowMA)

// Alert conditions
alertcondition(crossingUp, "Breadth crossing up from oversold", "{{ticker}} breadth crossing above oversold level")
alertcondition(crossingDown, "Breadth crossing down from overbought", "{{ticker}} breadth crossing below overbought level")
alertcondition(crossingMAUp, "Fast MA crossing up Slow MA", "{{ticker}} breadth fast MA crossing above slow MA")
alertcondition(crossingMADown, "Fast MA crossing down Slow MA", "{{ticker}} breadth fast MA crossing below slow MA")

// Display aggregate statistics
var table infoTable = table.new(position.bottom_right, 2, 2, border_width=1)
if barstate.islast
    table.cell(infoTable, 0, 0, "Active Strategies", bgcolor=color.new(#121212, 90), text_color=color.white)
    table.cell(infoTable, 1, 0, str.tostring(strategiesActive) + " / " + str.tostring(totalStrategies), bgcolor=color.new(#121212, 90), text_color=oscillatorColor)
    table.cell(infoTable, 0, 1, "Percentage", bgcolor=color.new(#121212, 90), text_color=color.white)
    table.cell(infoTable, 1, 1, str.tostring(math.round(strategyPercentage)) + "%", bgcolor=color.new(#121212, 90), text_color=oscillatorColor)
"""
    else:
        with open(template_path) as f:
            template = f.read()

    # Generate ticker counts string
    ticker_counts = []
    if ticker_filter:
        ticker_counts.append(f"// Filtered for ticker: {ticker_filter}")
    else:
        for ticker, count in ticker_strategy_counts.items():
            ticker_counts.append(f"// Strategies for {ticker}: {count}")

    # Replace placeholders
    pine_script = template.replace("{{STRATEGY_BLOCKS}}", strategy_blocks)
    pine_script = pine_script.replace("{{STRATEGY_COUNT}}", str(strategy_count))
    pine_script = pine_script.replace(
        "{{STRATEGY_COUNT_MINUS_1}}", str(strategy_count - 1)
    )
    pine_script = pine_script.replace("{{CSV_PATH}}", csv_path)
    pine_script = pine_script.replace(
        "{{GENERATION_DATE}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    pine_script = pine_script.replace(
        "{{DEFAULT_TICKER}}", ticker_options[0] if ticker_options else "BTC-USD"
    )
    pine_script = pine_script.replace("{{TICKER_OPTIONS}}", str(ticker_options))
    pine_script = pine_script.replace("{{TICKER_COUNTS}}", "\n".join(ticker_counts))

    return pine_script, strategy_count


def interactive_update(csv_path, pine_script_path, ticker_filter=None):
    """
    Interactive tool to update the Pine script with strategies from CSV file.

    Args:
        csv_path: Path to the CSV file containing strategy parameters
        pine_script_path: Path to the Pine script
        ticker_filter: Optional ticker symbol to filter strategies

    Returns:
        True if successful, False otherwise
    """
    try:
        # Generate hardcoded strategy blocks
        (
            strategy_blocks,
            strategy_count,
            _tickers,
            ticker_strategy_counts,
        ) = generate_hardcoded_strategies(csv_path, ticker_filter)

        # Create a backup of the original Pine script
        backup_path = (
            f"{pine_script_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        with open(pine_script_path) as f_in, open(backup_path, "w") as f_out:
            f_out.write(f_in.read())
        print(f"Created backup: {backup_path}")

        # Read Pine script
        with open(pine_script_path) as f:
            pine_script = f.read()

        # Find and replace strategy blocks
        start_marker = "calculateBreadth() =>"
        end_marker = (
            "// Return both the active strategies and the total applicable strategies"
        )

        start_index = pine_script.find(start_marker)
        if start_index == -1:
            print("Error: Could not find calculateBreadth() function in Pine script")
            return False

        start_index = pine_script.find("\n", start_index) + 1

        end_index = pine_script.find(end_marker, start_index)
        if end_index == -1:
            print("Error: Could not find end marker in Pine script")
            return False

        # Replace strategy blocks
        new_pine_script = pine_script[:start_index]
        new_pine_script += "    int strategiesInPosition = 0\n"
        new_pine_script += "    int totalApplicableStrategies = 0\n"
        new_pine_script += "    \n"
        new_pine_script += (
            "    // Process each strategy directly with hardcoded parameters\n"
        )
        new_pine_script += strategy_blocks
        new_pine_script += pine_script[end_index:]

        # Replace hline value and maxval in input parameters
        new_pine_script = new_pine_script.replace(
            'hline(11, "Max"', f'hline({strategy_count}, "Max"'
        )
        new_pine_script = new_pine_script.replace(
            "maxval=11", f"maxval={strategy_count}"
        )
        new_pine_script = new_pine_script.replace(
            "maxval=10", f"maxval={strategy_count - 1}"
        )

        # Update the strategy configuration comment
        config_marker = "// Strategy configuration"
        config_index = new_pine_script.find(config_marker)
        if config_index != -1:
            next_line_index = new_pine_script.find("\n", config_index) + 1
            config_end_index = new_pine_script.find("\n\n", next_line_index)

            config_comments = [
                "// Strategy configuration - Hardcoded directly in calculateBreadth() function",
                f"// Source: {csv_path}",
                f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"// Total strategies: {strategy_count}",
            ]

            if ticker_filter:
                config_comments.append(f"// Filtered for ticker: {ticker_filter}")
            else:
                for ticker, count in ticker_strategy_counts.items():
                    config_comments.append(f"// Strategies for {ticker}: {count}")

            new_config_section = "\n".join(config_comments) + "\n"
            new_pine_script = (
                new_pine_script[:next_line_index]
                + new_config_section
                + new_pine_script[config_end_index:]
            )

        # Write updated Pine script
        with open(pine_script_path, "w") as f:
            f.write(new_pine_script)

        print(f"\nPine script updated successfully: {pine_script_path}")
        print(f"Total strategies: {strategy_count}")
        return True

    except Exception as e:
        print(f"Error updating Pine script: {e}")
        return False


def main():
    """Main function to run the generator."""
    if len(sys.argv) < 2:
        print(
            "Usage: python generate_hardcoded_config.py <path_to_csv_file> [pine_script_path] [ticker_filter]"
        )
        print("\nOptions:")
        print("  path_to_csv_file: Path to the CSV file containing strategy parameters")
        print("  pine_script_path: Optional path to update an existing Pine script")
        print(
            "  ticker_filter: Optional ticker symbol to filter strategies (e.g., 'BTC-USD')"
        )
        print("\nExamples:")
        print("  # Generate a new Pine script from CSV:")
        print(
            "  python generate_hardcoded_config.py data/raw/strategies/BTC_d_20250427.csv"
        )
        print("\n  # Update an existing Pine script:")
        print(
            "  python generate_hardcoded_config.py data/raw/strategies/BTC_d_20250427.csv tradingview/strategy_breadth_refactored.pine"
        )
        print("\n  # Filter for a specific ticker:")
        print(
            "  python generate_hardcoded_config.py data/raw/strategies/BTC_d_20250427.csv tradingview/strategy_breadth_refactored.pine BTC-USD"
        )
        sys.exit(1)

    csv_path = sys.argv[1]
    pine_script_path = sys.argv[2] if len(sys.argv) > 2 else None
    ticker_filter = sys.argv[3] if len(sys.argv) > 3 else None

    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    if pine_script_path and os.path.exists(pine_script_path):
        # Update existing Pine script
        print(f"Updating existing Pine script: {pine_script_path}")
        if interactive_update(csv_path, pine_script_path, ticker_filter):
            print("Update completed successfully!")
        else:
            print("Update failed.")
            sys.exit(1)
    else:
        # Generate new Pine script
        print(f"Generating new Pine script from CSV: {csv_path}")
        pine_script, strategy_count = generate_pine_script_from_template(
            csv_path, None, ticker_filter
        )

        # Determine output filename
        ticker_part = f"_{ticker_filter}" if ticker_filter else ""
        filename = os.path.basename(csv_path)
        date_str = ""
        if "_" in filename and filename.endswith(".csv"):
            parts = filename.split("_")
            if len(parts) > 1:
                date_part = parts[-1].replace(".csv", "")
                if date_part.isdigit() and len(date_part) == 8:  # YYYYMMDD format
                    date_str = date_part

        # Ensure output file has .pine extension
        if pine_script_path:
            if not pine_script_path.endswith(".pine"):
                output_file = f"{pine_script_path}.pine"
            else:
                output_file = pine_script_path
        else:
            output_file = f"strategy_breadth_hardcoded{ticker_part}_{date_str or 'generated'}.pine"

        # Save to file
        with open(output_file, "w") as f:
            f.write(pine_script)

        print(f"\nPine script saved to {output_file}")
        print(f"Total strategies: {strategy_count}")


if __name__ == "__main__":
    main()

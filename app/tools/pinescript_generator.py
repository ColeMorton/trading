"""
PineScript Generator for Multi-Ticker Strategy Breadth Oscillators

This module generates PineScript indicator code from strategy CSV files,
creating ticker-specific breadth oscillators.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd


class PineScriptGenerator:
    """Generate PineScript code for multi-ticker strategy breadth oscillators."""

    def __init__(self, csv_path: str, ticker_filter: list[str] | None = None):
        """
        Initialize generator with strategy CSV file.

        Args:
            csv_path: Path to CSV file containing strategy data
            ticker_filter: Optional list of tickers to include
        """
        self.csv_path = Path(csv_path)
        self.df = pd.read_csv(csv_path)
        self._validate_csv()

        # Apply ticker filter if specified
        if ticker_filter:
            original_count = len(self.df)
            self.df = self.df[self.df["Ticker"].isin(ticker_filter)].copy()
            filtered_count = len(self.df)

            if filtered_count == 0:
                msg = f"No strategies found for tickers: {', '.join(ticker_filter)}"
                raise ValueError(
                    msg,
                )

            self.ticker_filter_applied = True
            self.ticker_filter_info = f"Filtered {original_count} strategies to {filtered_count} for tickers: {', '.join(ticker_filter)}"
        else:
            self.ticker_filter_applied = False
            self.ticker_filter_info = None

    def _validate_csv(self):
        """Validate CSV has required columns."""
        required_cols = ["Ticker", "Strategy Type", "Fast Period", "Slow Period"]
        missing_cols = [col for col in required_cols if col not in self.df.columns]
        if missing_cols:
            msg = f"CSV missing required columns: {missing_cols}"
            raise ValueError(msg)

    def _get_tickers(self) -> list[str]:
        """Get unique list of tickers from CSV."""
        return sorted(self.df["Ticker"].unique().tolist())

    def _get_ticker_strategies(self, ticker: str) -> pd.DataFrame:
        """Get strategies for a specific ticker."""
        return self.df[self.df["Ticker"] == ticker].copy()

    def _get_strategy_types(self, ticker: str) -> list[str]:
        """Get unique strategy types for a ticker."""
        strategies = self._get_ticker_strategies(ticker)
        return sorted(strategies["Strategy Type"].unique().tolist())

    def _generate_strategy_function(self, strategy: pd.Series) -> str:
        """Generate PineScript code for a single strategy check."""
        strategy_type = strategy["Strategy Type"]
        fast = int(strategy["Fast Period"])
        slow = int(strategy["Slow Period"])

        if strategy_type == "SMA":
            return (
                f"        if smaCrossSignal({fast}, {slow})\n            active += 1\n"
            )
        if strategy_type == "EMA":
            return (
                f"        if emaCrossSignal({fast}, {slow})\n            active += 1\n"
            )
        if strategy_type == "MACD":
            signal = int(strategy["Signal Period"])
            return f"        if macdSignal({fast}, {slow}, {signal})\n            active += 1\n"
        msg = f"Unknown strategy type: {strategy_type}"
        raise ValueError(msg)

    def _generate_ticker_block(self, ticker: str, strategies: pd.DataFrame) -> str:
        """Generate PineScript code block for a ticker's strategies."""
        total_strategies = len(strategies)

        # Determine if this is the first ticker (use 'if') or subsequent (use 'else if')
        tickers = self._get_tickers()
        condition = "if" if ticker == tickers[0] else "else if"

        code = f'    {condition} tickerInput == "{ticker}"\n'
        code += f"        total := {total_strategies}\n\n"

        for _idx, strategy in strategies.iterrows():
            code += self._generate_strategy_function(strategy)
            code += "\n"

        return code

    def _generate_header(self) -> str:
        """Generate PineScript file header with metadata."""
        tickers = self._get_tickers()
        total_strategies = len(self.df)

        header = "//@version=5\n"
        header += 'indicator("Multi-Ticker Strategy Breadth", shorttitle="Breadth", overlay=false)\n\n'
        header += "// ================ Script Metadata ================\n"
        header += f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"// Source CSV: {self.csv_path.name}\n"
        header += f"// Total Strategies: {total_strategies}\n"
        header += f"// Tickers: {', '.join(tickers)}\n"

        if self.ticker_filter_applied:
            header += "// Filter Applied: Yes\n"
            header += f"// {self.ticker_filter_info}\n"

        header += "\n"
        return header

    def _generate_config_section(self) -> str:
        """Generate configuration input section."""
        tickers = self._get_tickers()
        ticker_options = ", ".join([f'"{t}"' for t in tickers])

        config = "// ================ Configuration ================\n"
        config += f'tickerInput = input.string("{tickers[0]}", "Select Ticker", options=[{ticker_options}])\n'
        config += 'timeframeInput = input.timeframe("D", "Strategy Timeframe")\n'
        config += (
            'threshold = input.int(50, "Center Threshold", minval=0, maxval=100)\n\n'
        )
        return config

    def _generate_strategy_functions(self) -> str:
        """Generate reusable strategy calculation functions."""
        functions = "// ================ Strategy Functions ================\n\n"

        functions += "smaCrossSignal(shortWindow, longWindow) =>\n"
        functions += "    shortSMA = ta.sma(close, shortWindow)\n"
        functions += "    longSMA = ta.sma(close, longWindow)\n"
        functions += "    shortSMA > longSMA\n\n"

        functions += "emaCrossSignal(shortWindow, longWindow) =>\n"
        functions += "    shortEMA = ta.ema(close, shortWindow)\n"
        functions += "    longEMA = ta.ema(close, longWindow)\n"
        functions += "    shortEMA > longEMA\n\n"

        functions += "macdSignal(shortWindow, longWindow, signalWindow) =>\n"
        functions += "    [macdLine, signalLine, _] = ta.macd(close, shortWindow, longWindow, signalWindow)\n"
        functions += "    macdLine > signalLine\n\n"

        return functions

    def _generate_calculation_logic(self) -> str:
        """Generate main breadth calculation logic with ticker switching."""
        logic = "// ================ Breadth Calculation ================\n"
        logic += "calculateBreadth() =>\n"
        logic += "    int active = 0\n"
        logic += "    int total = 0\n\n"

        # Generate blocks for each ticker
        for ticker in self._get_tickers():
            strategies = self._get_ticker_strategies(ticker)
            logic += self._generate_ticker_block(ticker, strategies)

        logic += "    [active, total]\n\n"

        # Add request.security call
        logic += "// Execute calculation on selected timeframe\n"
        logic += "[active, total] = request.security(syminfo.tickerid, timeframeInput, calculateBreadth())\n"
        logic += "percentage = (active / total) * 100\n\n"

        return logic

    def _generate_visualization(self) -> str:
        """Generate visualization and plotting code."""
        viz = "// ================ Visualization ================\n\n"

        # Colors
        viz += "color bullColor = color.new(#26c6da, 0)\n"
        viz += "color bearColor = color.new(#7e57c2, 0)\n"
        viz += "color neutralColor = color.new(#3179f5, 0)\n\n"

        # Dynamic coloring
        viz += "oscillatorColor = percentage > threshold ? bullColor : \n"
        viz += "                  percentage < threshold ? bearColor : \n"
        viz += "                  neutralColor\n\n"

        # Main plot
        viz += "// Plot oscillator\n"
        viz += 'plot(percentage, "Strategy Breadth %", color=oscillatorColor, linewidth=2)\n'
        viz += 'hline(threshold, "Threshold", color=neutralColor, linestyle=hline.style_dashed)\n\n'

        # Info table
        viz += "// Display statistics table\n"
        viz += "var table infoTable = table.new(position.bottom_right, 2, 2, border_width=1)\n"
        viz += "if barstate.islast\n"
        viz += '    table.cell(infoTable, 0, 0, "Active Strategies", bgcolor=color.new(#000000, 90), text_color=color.white)\n'
        viz += '    table.cell(infoTable, 1, 0, str.tostring(active) + " / " + str.tostring(total), bgcolor=color.new(#000000, 90), text_color=oscillatorColor)\n'
        viz += '    table.cell(infoTable, 0, 1, "Percentage", bgcolor=color.new(#000000, 90), text_color=color.white)\n'
        viz += '    table.cell(infoTable, 1, 1, str.tostring(math.round(percentage)) + "%", bgcolor=color.new(#000000, 90), text_color=oscillatorColor)\n\n'

        return viz

    def _generate_alerts(self) -> str:
        """Generate alert conditions."""
        alerts = "// ================ Alerts ================\n"
        alerts += "crossingUp = ta.crossover(percentage, threshold)\n"
        alerts += "crossingDown = ta.crossunder(percentage, threshold)\n\n"
        alerts += 'alertcondition(crossingUp, "Breadth Crossing Up", "{{ticker}} breadth crossing above threshold")\n'
        alerts += 'alertcondition(crossingDown, "Breadth Crossing Down", "{{ticker}} breadth crossing below threshold")\n'
        return alerts

    def generate(self, output_path: str | None = None) -> str:
        """
        Generate complete PineScript code.

        Args:
            output_path: Optional path to save generated code

        Returns:
            Generated PineScript code as string
        """
        # Assemble all sections
        code = self._generate_header()
        code += self._generate_config_section()
        code += self._generate_strategy_functions()
        code += self._generate_calculation_logic()
        code += self._generate_visualization()
        code += self._generate_alerts()

        # Save to file if requested
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(code)

        return code

    def get_stats(self) -> dict:
        """Get generation statistics."""
        tickers = self._get_tickers()
        stats = {
            "total_strategies": len(self.df),
            "total_tickers": len(tickers),
            "tickers": tickers,
            "strategies_per_ticker": {},
            "strategy_types_per_ticker": {},
        }

        for ticker in tickers:
            ticker_strategies = self._get_ticker_strategies(ticker)
            stats["strategies_per_ticker"][ticker] = len(ticker_strategies)
            stats["strategy_types_per_ticker"][ticker] = self._get_strategy_types(
                ticker,
            )

        return stats

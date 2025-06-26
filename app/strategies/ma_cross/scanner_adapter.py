"""
Scanner Adapter Module

This module provides an adapter that allows the existing scanner functionality
to be used programmatically without file I/O dependencies.
"""

import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import polars as pl

from app.strategies.ma_cross.core import (
    AnalysisConfig,
    AnalysisResult,
    SignalInfo,
    TickerResult,
)
from app.strategies.ma_cross.core.analyzer import MACrossAnalyzer
from app.strategies.ma_cross.tools.scanner_processing import process_ticker
from app.tools.setup_logging import setup_logging


class ScannerAdapter:
    """
    Adapter class that wraps the existing scanner functionality
    for programmatic use.
    """

    def __init__(self, log: Optional[Callable] | None = None):
        """Initialize the scanner adapter."""
        self._log = log
        self._log_close = None

        if self._log is None:
            self._log, self._log_close, _, _ = setup_logging(
                "ma_cross_scanner_adapter", "scanner_adapter.log"
            )

    def process_portfolio_file(
        self, portfolio_path: str, config: Dict[str, Any]
    ) -> AnalysisResult:
        """
        Process a portfolio CSV file using the existing scanner logic.

        Args:
            portfolio_path: Path to portfolio CSV file
            config: Configuration dictionary

        Returns:
            AnalysisResult with signals for all tickers
        """
        try:
            # Read portfolio file
            scanner_df = pl.read_csv(
                portfolio_path,
                infer_schema_length=10000,
                try_parse_dates=True,
                ignore_errors=True,
                truncate_ragged_lines=True,
                schema_overrides={
                    "Start Value": pl.Float64,
                    "End Value": pl.Float64,
                    "Return": pl.Float64,
                    "Annual Return": pl.Float64,
                    "Sharpe Ratio": pl.Float64,
                    "Max Drawdown": pl.Float64,
                    "Calmar Ratio": pl.Float64,
                    "Recovery Factor": pl.Float64,
                    "Profit Factor": pl.Float64,
                    "Common Sense Ratio": pl.Float64,
                    "Win Rate": pl.Float64,
                    "Short Window": pl.Int64,
                    "Long Window": pl.Int64,
                },
            )

            # Process each row using existing scanner logic
            results = []
            ticker_col = "Ticker" if "Ticker" in scanner_df.columns else "TICKER"

            for row in scanner_df.iter_rows(named=True):
                ticker = row[ticker_col]
                ticker_results = self._process_ticker_row(ticker, row, config)
                if ticker_results:
                    results.extend(ticker_results)

            return AnalysisResult(
                tickers=results,
                total_processing_time=0.0,  # Would need timing logic
                analysis_date=datetime.now(),
            )

        except Exception as e:
            self._log(f"Error processing portfolio file: {str(e)}", "error")
            raise

    def _process_ticker_row(
        self, ticker: str, row: Dict[str, Any], config: Dict[str, Any]
    ) -> List[TickerResult]:
        """
        Process a single row from the portfolio using existing scanner logic.

        Returns list of TickerResult objects (one for SMA, one for EMA if applicable).
        """
        results = []

        try:
            # Use existing process_ticker function
            result = process_ticker(ticker, row, config, self._log)

            if result:
                # Convert scanner result to TickerResult objects
                from app.strategies.ma_cross.core.models import SignalInfo

                # Check SMA signal
                if result.get("SMA"):
                    sma_result = TickerResult(ticker=ticker)
                    sma_result.signals.append(
                        SignalInfo(
                            ma_type="SMA",
                            short_window=result.get("SMA_FAST", 0),
                            long_window=result.get("SMA_SLOW", 0),
                            signal_date=datetime.now(),
                            signal_type="BUY",  # Would need to determine from actual data
                            current=True,
                        )
                    )
                    results.append(sma_result)

                # Check EMA signal
                if result.get("EMA"):
                    ema_result = TickerResult(ticker=ticker)
                    ema_result.signals.append(
                        SignalInfo(
                            ma_type="EMA",
                            short_window=result.get("EMA_FAST", 0),
                            long_window=result.get("EMA_SLOW", 0),
                            signal_date=datetime.now(),
                            signal_type="BUY",  # Would need to determine from actual data
                            current=True,
                        )
                    )
                    results.append(ema_result)

        except Exception as e:
            self._log(f"Error processing {ticker}: {str(e)}", "error")
            # Return error result
            error_result = TickerResult(ticker=ticker, error=str(e))
            results.append(error_result)

        return results

    def close(self):
        """Clean up resources."""
        if self._log_close:
            self._log_close()

    def _json_to_config(self, json_portfolio: Dict[str, Any]) -> AnalysisConfig:
        """
        Convert JSON portfolio format to AnalysisConfig.

        Args:
            json_portfolio: Portfolio in JSON format

        Returns:
            AnalysisConfig instance
        """
        # Extract first ticker from symbols list
        ticker = json_portfolio.get("symbols", ["UNKNOWN"])[0]

        # Extract MA type (default to SMA)
        ma_types = json_portfolio.get("ma_types", ["SMA"])
        use_sma = ma_types[0].upper() == "SMA" if ma_types else True

        # Extract periods
        fast_periods = json_portfolio.get("fast_periods", [20])
        slow_periods = json_portfolio.get("slow_periods", [50])

        # Extract timeframe (convert to hourly if needed)
        timeframes = json_portfolio.get("timeframes", ["D"])
        use_hourly = timeframes[0].upper() == "H" if timeframes else False

        return AnalysisConfig(
            ticker=ticker,
            use_sma=use_sma,
            short_window=fast_periods[0] if fast_periods else 20,
            long_window=slow_periods[0] if slow_periods else 50,
            use_hourly=use_hourly,
            direction="Long",  # Default to Long
        )

    def scan_portfolio(self, json_portfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan a portfolio and return results in the expected format.

        Args:
            json_portfolio: Portfolio configuration in JSON format

        Returns:
            List of result dictionaries with symbol and metrics
        """
        results = []

        # Get list of symbols to process
        symbols = json_portfolio.get("symbols", [])

        # Create analyzer
        analyzer = MACrossAnalyzer(log=self._log)

        try:
            for symbol in symbols:
                # Create config for this symbol
                config = self._json_to_config(json_portfolio)
                config.ticker = symbol  # Override ticker

                # Analyze the ticker
                ticker_result = analyzer.analyze_single(config)

                # Format result for output
                result_dict = {
                    "symbol": symbol,
                    "total_return": getattr(ticker_result, "total_return_pct", 0.0),
                    "sharpe_ratio": getattr(ticker_result, "sharpe_ratio", 0.0),
                    "max_drawdown": getattr(ticker_result, "max_drawdown_pct", 0.0),
                    "win_rate": getattr(ticker_result, "win_rate_pct", 0.0),
                    "total_trades": getattr(ticker_result, "total_trades", 0),
                    "strategy_type": getattr(ticker_result, "strategy_type", "SMA"),
                    "short_window": config.short_window,
                    "long_window": config.long_window,
                }

                results.append(result_dict)

        finally:
            analyzer.close()

        return results

    def _convert_timeframe(self, timeframe: str) -> str:
        """
        Convert portfolio timeframe to yfinance interval format.

        Args:
            timeframe: Timeframe string (D, H, W, M)

        Returns:
            yfinance interval string

        Raises:
            ValueError: If timeframe is invalid
        """
        mapping = {"D": "1d", "H": "1h", "W": "1wk", "M": "1mo"}

        upper_tf = timeframe.upper()
        if upper_tf not in mapping:
            raise ValueError(f"Invalid timeframe: {timeframe}")

        return mapping[upper_tf]

    def _format_result(self, portfolio_result: TickerResult) -> Dict[str, Any]:
        """
        Format a TickerResult for CLI output.

        Args:
            portfolio_result: TickerResult instance

        Returns:
            Formatted dictionary
        """
        return {
            "ticker": portfolio_result.ticker,
            "total_return_pct": getattr(portfolio_result, "total_return_pct", 0.0),
            "sharpe_ratio": getattr(portfolio_result, "sharpe_ratio", 0.0),
            "max_drawdown_pct": getattr(portfolio_result, "max_drawdown_pct", 0.0),
            "win_rate_pct": getattr(portfolio_result, "win_rate_pct", 0.0),
            "total_trades": getattr(portfolio_result, "total_trades", 0),
            "profit_factor": getattr(portfolio_result, "profit_factor", 0.0),
            "sortino_ratio": getattr(portfolio_result, "sortino_ratio", 0.0),
            "strategy_type": getattr(portfolio_result, "strategy_type", "SMA"),
            "short_window": getattr(portfolio_result, "short_window", 0),
            "long_window": getattr(portfolio_result, "long_window", 0),
            "beats_bnh_pct": getattr(portfolio_result, "beats_bnh_pct", 0.0),
            "expectancy_per_trade": getattr(
                portfolio_result, "expectancy_per_trade", 0.0
            ),
        }


def run_scanner_with_config(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convenience function to run the scanner with a given configuration
    and return results as dictionaries.

    Args:
        config: Configuration dictionary with PORTFOLIO and other settings

    Returns:
        List of signal dictionaries
    """
    adapter = ScannerAdapter()

    try:
        portfolio_path = os.path.join("./csv/strategies", config["PORTFOLIO"])
        result = adapter.process_portfolio_file(portfolio_path, config)

        # Convert to list of dictionaries for compatibility
        signals = []
        for ticker_result in result.tickers:
            if ticker_result.has_current_signal:
                for signal in ticker_result.current_signals:
                    signals.append(
                        {
                            "ticker": ticker_result.ticker,
                            "ma_type": signal.ma_type,
                            "short_window": signal.short_window,
                            "long_window": signal.long_window,
                            "signal_date": signal.signal_date.isoformat(),
                            "signal_type": signal.signal_type,
                            "current": signal.current,
                        }
                    )

        return signals

    finally:
        adapter.close()

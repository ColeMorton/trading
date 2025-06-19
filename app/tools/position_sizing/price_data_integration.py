"""
Price Data Integration for Position Sizing

This module provides a standardized interface for price data fetching using existing
@app/tools/get_data.py and @app/tools/download_data.py infrastructure.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import polars as pl

from app.tools.data_types import DataConfig
from app.tools.get_data import get_data


class PriceDataIntegration:
    """Standardized price data interface for position sizing calculations."""

    def __init__(self, base_dir: Optional[str] = None, cache_enabled: bool = True):
        """Initialize price data integration.

        Args:
            base_dir: Base directory path. If None, uses current working directory.
            cache_enabled: Whether to use cached data when available.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.cache_enabled = cache_enabled

    def _create_config(
        self, refresh: bool = False, use_hourly: bool = False, period: str = "max"
    ) -> DataConfig:
        """Create standardized data configuration.

        Args:
            refresh: Whether to force data refresh
            use_hourly: Whether to use hourly data instead of daily
            period: Data period ('max', '1y', '6mo', etc.)

        Returns:
            Data configuration dictionary
        """
        return {
            "BASE_DIR": str(self.base_dir),
            "REFRESH": refresh or not self.cache_enabled,
            "USE_HOURLY": use_hourly,
            "PERIOD": period,
            "USE_SYNTHETIC": False,
            "USE_GBM": False,
        }

    def _silent_log(self, message: str, level: str = "info"):
        """Silent logging function for internal data fetching."""
        pass

    def get_current_price(self, symbol: str, use_cache: bool = True) -> float:
        """Get current/latest price for a single symbol.

        Args:
            symbol: Asset symbol (e.g., 'AAPL', 'BTC-USD')
            use_cache: Whether to use cached data

        Returns:
            Latest close price

        Raises:
            ValueError: If no price data is available
        """
        config = self._create_config(refresh=not use_cache, period="5d")

        try:
            data = get_data(symbol, config, self._silent_log)

            # Handle synthetic ticker case
            if isinstance(data, tuple):
                data, _ = data

            # Get latest close price
            if len(data) > 0:
                return float(data["Close"].tail(1).item())
            else:
                raise ValueError(f"No price data available for {symbol}")

        except Exception as e:
            raise ValueError(f"Failed to fetch price for {symbol}: {str(e)}")

    def get_multiple_prices(
        self, symbols: List[str], use_cache: bool = True
    ) -> Dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of asset symbols
            use_cache: Whether to use cached data

        Returns:
            Dictionary mapping symbols to current prices
        """
        prices = {}
        errors = []

        for symbol in symbols:
            try:
                prices[symbol] = self.get_current_price(symbol, use_cache)
            except Exception as e:
                errors.append(f"{symbol}: {str(e)}")
                prices[symbol] = 0.0

        if errors:
            print(
                f"Warning: Failed to fetch prices for some symbols: {'; '.join(errors)}"
            )

        return prices

    def get_historical_data(
        self, symbol: str, period: str = "1y", use_hourly: bool = False
    ) -> pl.DataFrame:
        """Get historical price data for analysis.

        Args:
            symbol: Asset symbol
            period: Data period ('1y', '6mo', 'max', etc.)
            use_hourly: Whether to use hourly data

        Returns:
            Polars DataFrame with historical OHLCV data
        """
        config = self._create_config(
            refresh=False, use_hourly=use_hourly, period=period
        )

        data = get_data(symbol, config, self._silent_log)

        # Handle synthetic ticker case
        if isinstance(data, tuple):
            data, _ = data

        return data

    def calculate_price_changes(self, symbol: str, days: int = 30) -> Dict[str, float]:
        """Calculate price change metrics for a symbol.

        Args:
            symbol: Asset symbol
            days: Number of days to analyze

        Returns:
            Dictionary containing price change metrics
        """
        try:
            data = self.get_historical_data(symbol, period=f"{days*2}d")

            if len(data) < days:
                raise ValueError(f"Insufficient data for {symbol}")

            # Get recent and historical prices
            current_price = float(data["Close"].tail(1).item())
            price_n_days_ago = float(data["Close"].tail(days + 1).head(1).item())

            # Calculate metrics
            absolute_change = current_price - price_n_days_ago
            percentage_change = (absolute_change / price_n_days_ago) * 100

            # Calculate volatility (standard deviation of daily returns)
            returns = data["Close"].pct_change().drop_nulls()
            volatility = float(returns.std()) * 100  # Convert to percentage

            return {
                "current_price": current_price,
                "price_n_days_ago": price_n_days_ago,
                "absolute_change": absolute_change,
                "percentage_change": percentage_change,
                "volatility_pct": volatility,
                "data_points": len(data),
            }

        except Exception as e:
            raise ValueError(
                f"Failed to calculate price changes for {symbol}: {str(e)}"
            )

    def validate_symbol(self, symbol: str) -> Tuple[bool, str]:
        """Validate that a symbol has available price data.

        Args:
            symbol: Asset symbol to validate

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            price = self.get_current_price(symbol)
            if price > 0:
                return True, f"Valid symbol with current price: ${price:.2f}"
            else:
                return False, f"Symbol has zero price: {symbol}"

        except Exception as e:
            return False, f"Invalid symbol {symbol}: {str(e)}"

    def get_portfolio_prices(self, portfolio: Dict[str, float]) -> Dict[str, any]:
        """Get prices and calculate values for a portfolio.

        Args:
            portfolio: Dictionary mapping symbols to quantities/allocations

        Returns:
            Dictionary containing portfolio pricing information
        """
        symbols = list(portfolio.keys())
        prices = self.get_multiple_prices(symbols)

        portfolio_data = {}
        total_value = 0.0

        for symbol, quantity in portfolio.items():
            price = prices.get(symbol, 0.0)
            value = price * quantity
            total_value += value

            portfolio_data[symbol] = {
                "quantity": quantity,
                "price": price,
                "value": value,
            }

        portfolio_data["_total_value"] = total_value
        portfolio_data["_timestamp"] = pl.datetime.now()

        return portfolio_data

    def refresh_all_cache(self, symbols: List[str]) -> Dict[str, bool]:
        """Force refresh cached data for multiple symbols.

        Args:
            symbols: List of symbols to refresh

        Returns:
            Dictionary mapping symbols to success status
        """
        results = {}

        for symbol in symbols:
            try:
                self.get_current_price(symbol, use_cache=False)
                results[symbol] = True
            except Exception:
                results[symbol] = False

        return results

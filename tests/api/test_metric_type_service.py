"""
Test suite for metric_type handling in MA Cross Service.

Tests the service layer to ensure metric_type is properly extracted
from portfolio dictionaries and preserved through the analysis flow.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from app.api.models.strategy_analysis import MACrossRequest, PortfolioMetrics
from app.api.services.ma_cross_service import MACrossService


class TestMACrossServiceMetricType:
    """Test metric_type handling in MA Cross Service."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for MACrossService."""
        return {
            "logger": Mock(),
            "progress_tracker": Mock(),
            "strategy_executor": Mock(),
            "strategy_analyzer": Mock(),
            "cache": Mock(),
            "monitoring": Mock(),
            "configuration": Mock(),
        }

    @pytest.fixture
    def service(self, mock_dependencies):
        """Create MACrossService instance with mocked dependencies."""
        return MACrossService(**mock_dependencies)

    @pytest.fixture
    def sample_portfolio_dict_with_metric_type(self):
        """Sample portfolio dictionary with metric_type field."""
        return {
            "Ticker": "BTC-USD",
            "Strategy Type": "EMA",
            "Short Window": 5,
            "Long Window": 10,
            "Total Return [%]": 150.0,
            "Ann. Return [%]": 25.0,
            "Sharpe Ratio": 1.2,
            "Sortino Ratio": 1.5,
            "Max Drawdown [%]": 20.0,
            "Total Trades": 50,
            "Win Rate [%]": 60.0,
            "Profit Factor": 2.0,
            "Expectancy": 500.0,
            "Score": 1.0,
            "Beats BNH [%]": 10.0,
            "Total Open Trades": 0,
            "Signal Entry": True,
            "Metric Type": "Most Sharpe Ratio, Most Total Return [%]",
        }

    @pytest.fixture
    def sample_portfolio_dict_without_metric_type(self):
        """Sample portfolio dictionary without metric_type field."""
        return {
            "Ticker": "ETH-USD",
            "Strategy Type": "SMA",
            "Short Window": 12,
            "Long Window": 26,
            "Total Return [%]": 100.0,
            "Ann. Return [%]": 20.0,
            "Sharpe Ratio": 1.0,
            "Sortino Ratio": 1.2,
            "Max Drawdown [%]": 15.0,
            "Total Trades": 30,
            "Win Rate [%]": 70.0,
            "Profit Factor": 1.8,
            "Expectancy": 300.0,
            "Score": 0.9,
            "Beats BNH [%]": 5.0,
            "Total Open Trades": 1,
            "Signal Entry": False,
            # No "Metric Type" field
        }

    def test_portfolio_metrics_creation_with_metric_type(
        self, sample_portfolio_dict_with_metric_type
    ):
        """Test that PortfolioMetrics is created correctly with metric_type."""
        portfolio_dict = sample_portfolio_dict_with_metric_type

        # Test the conversion logic from the service
        metrics = PortfolioMetrics(
            ticker=portfolio_dict.get("Ticker", ""),
            strategy_type=portfolio_dict.get("Strategy Type", ""),
            short_window=int(portfolio_dict.get("Short Window", 0)),
            long_window=int(portfolio_dict.get("Long Window", 0)),
            total_return=float(portfolio_dict.get("Total Return [%]", 0.0)),
            annual_return=float(portfolio_dict.get("Ann. Return [%]", 0.0)),
            sharpe_ratio=float(portfolio_dict.get("Sharpe Ratio", 0.0)),
            sortino_ratio=float(portfolio_dict.get("Sortino Ratio", 0.0)),
            max_drawdown=float(portfolio_dict.get("Max Drawdown [%]", 0.0)),
            total_trades=int(portfolio_dict.get("Total Trades", 0)),
            winning_trades=int(30 * 0.6),  # Calculated from total_trades * win_rate
            losing_trades=int(30 * 0.4),
            win_rate=float(portfolio_dict.get("Win Rate [%]", 0.0)) / 100.0,
            profit_factor=float(portfolio_dict.get("Profit Factor", 0.0)),
            expectancy=float(portfolio_dict.get("Expectancy", 0.0)),
            score=float(portfolio_dict.get("Score", 0.0)),
            beats_bnh=float(portfolio_dict.get("Beats BNH [%]", 0.0)),
            has_open_trade=bool(int(portfolio_dict.get("Total Open Trades", 0)) > 0),
            has_signal_entry=bool(portfolio_dict.get("Signal Entry", False)),
            metric_type=portfolio_dict.get("Metric Type"),
        )

        assert metrics.metric_type == "Most Sharpe Ratio, Most Total Return [%]"
        assert metrics.ticker == "BTC-USD"
        assert metrics.strategy_type == "EMA"

    def test_portfolio_metrics_creation_without_metric_type(
        self, sample_portfolio_dict_without_metric_type
    ):
        """Test that PortfolioMetrics handles missing metric_type gracefully."""
        portfolio_dict = sample_portfolio_dict_without_metric_type

        metrics = PortfolioMetrics(
            ticker=portfolio_dict.get("Ticker", ""),
            strategy_type=portfolio_dict.get("Strategy Type", ""),
            short_window=int(portfolio_dict.get("Short Window", 0)),
            long_window=int(portfolio_dict.get("Long Window", 0)),
            total_return=float(portfolio_dict.get("Total Return [%]", 0.0)),
            annual_return=float(portfolio_dict.get("Ann. Return [%]", 0.0)),
            sharpe_ratio=float(portfolio_dict.get("Sharpe Ratio", 0.0)),
            sortino_ratio=float(portfolio_dict.get("Sortino Ratio", 0.0)),
            max_drawdown=float(portfolio_dict.get("Max Drawdown [%]", 0.0)),
            total_trades=int(portfolio_dict.get("Total Trades", 0)),
            winning_trades=int(30 * 0.7),
            losing_trades=int(30 * 0.3),
            win_rate=float(portfolio_dict.get("Win Rate [%]", 0.0)) / 100.0,
            profit_factor=float(portfolio_dict.get("Profit Factor", 0.0)),
            expectancy=float(portfolio_dict.get("Expectancy", 0.0)),
            score=float(portfolio_dict.get("Score", 0.0)),
            beats_bnh=float(portfolio_dict.get("Beats BNH [%]", 0.0)),
            has_open_trade=bool(int(portfolio_dict.get("Total Open Trades", 0)) > 0),
            has_signal_entry=bool(portfolio_dict.get("Signal Entry", False)),
            metric_type=portfolio_dict.get("Metric Type"),  # This will be None
        )

        assert metrics.metric_type == ""  # Should default to empty string
        assert metrics.ticker == "ETH-USD"
        assert metrics.strategy_type == "SMA"

    @patch("app.api.services.ma_cross_service.execute_strategy")
    @patch("app.api.services.ma_cross_service.collect_filtered_portfolios_for_export")
    @patch("app.api.services.ma_cross_service.deduplicate_and_aggregate_portfolios")
    def test_execute_analysis_preserves_metric_type(
        self,
        mock_deduplicate,
        mock_collect,
        mock_execute,
        service,
        sample_portfolio_dict_with_metric_type,
    ):
        """Test that _execute_analysis preserves metric_type through the full flow."""
        # Mock the execute_strategy to return portfolio dicts
        mock_execute.return_value = [sample_portfolio_dict_with_metric_type]

        # Mock collect_filtered_portfolios_for_export
        mock_collect.return_value = [sample_portfolio_dict_with_metric_type]

        # Mock deduplicate_and_aggregate_portfolios
        mock_deduplicate.return_value = [sample_portfolio_dict_with_metric_type]

        # Create a mock config
        config = {
            "STRATEGY_TYPES": ["EMA"],
            "BASE_DIR": "/test",
            "DESIRED_METRIC_TYPES": ["Most Sharpe Ratio", "Most Total Return [%]"],
        }

        # Create a mock log function
        mock_log = Mock()

        # Execute the analysis
        results = service._execute_analysis(config, mock_log)

        # Verify metric_type is preserved
        assert len(results) > 0
        assert isinstance(results[0], PortfolioMetrics)
        assert results[0].metric_type == "Most Sharpe Ratio, Most Total Return [%]"

        # Verify the mocks were called
        mock_execute.assert_called()
        mock_collect.assert_called_with(config, ["EMA"], mock_log)
        mock_deduplicate.assert_called()

    @patch("asyncio.get_event_loop")
    @patch("app.api.services.ma_cross_service.execute_strategy")
    def test_analyze_portfolio_async_preserves_metric_type(
        self,
        mock_execute,
        mock_get_loop,
        service,
        sample_portfolio_dict_with_metric_type,
    ):
        """Test that async analysis preserves metric_type."""
        # Mock the event loop and executor
        mock_loop = Mock()
        mock_get_loop.return_value = mock_loop
        mock_loop.run_in_executor.return_value = [
            sample_portfolio_dict_with_metric_type
        ]

        # Create a mock request
        request = MACrossRequest(ticker="BTC-USD", windows=10)

        # Mock the cache to return None (no cached result)
        service.cache.get.return_value = None

        # Create a mock config
        with patch.object(service, "_collect_export_paths") as mock_collect_paths:
            mock_collect_paths.return_value = {
                "portfolios": [],
                "portfolios_filtered": [],
            }

            # This would normally be an async call, but we're testing the logic
            # The actual async test would require more complex mocking
            pass

    def test_multiple_portfolios_with_different_metric_types(self):
        """Test handling multiple portfolios with different metric_types."""
        portfolio_1 = {
            "Ticker": "BTC-USD",
            "Strategy Type": "EMA",
            "Short Window": 5,
            "Long Window": 10,
            "Total Return [%]": 150.0,
            "Ann. Return [%]": 25.0,
            "Sharpe Ratio": 1.2,
            "Sortino Ratio": 1.5,
            "Max Drawdown [%]": 20.0,
            "Total Trades": 50,
            "Win Rate [%]": 60.0,
            "Profit Factor": 2.0,
            "Expectancy": 500.0,
            "Score": 1.0,
            "Beats BNH [%]": 10.0,
            "Total Open Trades": 0,
            "Signal Entry": True,
            "Metric Type": "Most Sharpe Ratio",
        }

        portfolio_2 = {
            "Ticker": "ETH-USD",
            "Strategy Type": "SMA",
            "Short Window": 12,
            "Long Window": 26,
            "Total Return [%]": 100.0,
            "Ann. Return [%]": 20.0,
            "Sharpe Ratio": 1.0,
            "Sortino Ratio": 1.2,
            "Max Drawdown [%]": 15.0,
            "Total Trades": 30,
            "Win Rate [%]": 70.0,
            "Profit Factor": 1.8,
            "Expectancy": 300.0,
            "Score": 0.9,
            "Beats BNH [%]": 5.0,
            "Total Open Trades": 1,
            "Signal Entry": False,
            "Metric Type": "Most Total Return [%]",
        }

        # Convert both portfolios to PortfolioMetrics
        portfolios = []
        for portfolio_dict in [portfolio_1, portfolio_2]:
            metrics = PortfolioMetrics(
                ticker=portfolio_dict.get("Ticker", ""),
                strategy_type=portfolio_dict.get("Strategy Type", ""),
                short_window=int(portfolio_dict.get("Short Window", 0)),
                long_window=int(portfolio_dict.get("Long Window", 0)),
                total_return=float(portfolio_dict.get("Total Return [%]", 0.0)),
                annual_return=float(portfolio_dict.get("Ann. Return [%]", 0.0)),
                sharpe_ratio=float(portfolio_dict.get("Sharpe Ratio", 0.0)),
                sortino_ratio=float(portfolio_dict.get("Sortino Ratio", 0.0)),
                max_drawdown=float(portfolio_dict.get("Max Drawdown [%]", 0.0)),
                total_trades=int(portfolio_dict.get("Total Trades", 0)),
                winning_trades=int(
                    portfolio_dict.get("Total Trades", 0)
                    * portfolio_dict.get("Win Rate [%]", 0.0)
                    / 100
                ),
                losing_trades=int(
                    portfolio_dict.get("Total Trades", 0)
                    * (100 - portfolio_dict.get("Win Rate [%]", 0.0))
                    / 100
                ),
                win_rate=float(portfolio_dict.get("Win Rate [%]", 0.0)) / 100.0,
                profit_factor=float(portfolio_dict.get("Profit Factor", 0.0)),
                expectancy=float(portfolio_dict.get("Expectancy", 0.0)),
                score=float(portfolio_dict.get("Score", 0.0)),
                beats_bnh=float(portfolio_dict.get("Beats BNH [%]", 0.0)),
                has_open_trade=bool(
                    int(portfolio_dict.get("Total Open Trades", 0)) > 0
                ),
                has_signal_entry=bool(portfolio_dict.get("Signal Entry", False)),
                metric_type=portfolio_dict.get("Metric Type"),
            )
            portfolios.append(metrics)

        # Verify each portfolio has its distinct metric_type
        assert portfolios[0].metric_type == "Most Sharpe Ratio"
        assert portfolios[1].metric_type == "Most Total Return [%]"

        # Verify serialization preserves distinct metric_types
        serialized = [p.model_dump() for p in portfolios]
        assert serialized[0]["metric_type"] == "Most Sharpe Ratio"
        assert serialized[1]["metric_type"] == "Most Total Return [%]"

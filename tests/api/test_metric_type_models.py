"""
Test suite for metric_type field in Pydantic models.

Tests the PortfolioMetrics model serialization and deserialization
to ensure metric_type field is properly handled.
"""

import pytest

from app.api.models.strategy_analysis import PortfolioMetrics


class TestPortfolioMetricsMetricType:
    """Test metric_type field handling in PortfolioMetrics model."""

    def test_metric_type_field_exists(self):
        """Test that metric_type field is defined in the model."""
        # Create a minimal PortfolioMetrics instance
        portfolio = PortfolioMetrics(
            ticker="TEST",
            strategy_type="SMA",
            short_window=5,
            long_window=10,
            total_return=10.0,
            annual_return=5.0,
            sharpe_ratio=1.0,
            sortino_ratio=1.2,
            max_drawdown=5.0,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.6,
            profit_factor=1.5,
            expectancy=100.0,
            score=1.0,
            beats_bnh=5.0,
            metric_type="Most Total Return [%]",
        )

        assert hasattr(portfolio, "metric_type")
        assert portfolio.metric_type == "Most Total Return [%]"

    def test_metric_type_default_value(self):
        """Test that metric_type defaults to empty string."""
        portfolio = PortfolioMetrics(
            ticker="TEST",
            strategy_type="SMA",
            short_window=5,
            long_window=10,
            total_return=10.0,
            annual_return=5.0,
            sharpe_ratio=1.0,
            sortino_ratio=1.2,
            max_drawdown=5.0,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.6,
            profit_factor=1.5,
            expectancy=100.0,
            score=1.0,
            beats_bnh=5.0,
            # metric_type not provided
        )

        assert portfolio.metric_type == ""

    def test_metric_type_none_value(self):
        """Test that metric_type can be None and defaults to empty string."""
        portfolio = PortfolioMetrics(
            ticker="TEST",
            strategy_type="SMA",
            short_window=5,
            long_window=10,
            total_return=10.0,
            annual_return=5.0,
            sharpe_ratio=1.0,
            sortino_ratio=1.2,
            max_drawdown=5.0,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.6,
            profit_factor=1.5,
            expectancy=100.0,
            score=1.0,
            beats_bnh=5.0,
            metric_type=None,
        )

        assert portfolio.metric_type == ""

    def test_model_dump_includes_metric_type(self):
        """Test that model_dump() includes metric_type field."""
        portfolio = PortfolioMetrics(
            ticker="TEST",
            strategy_type="SMA",
            short_window=5,
            long_window=10,
            total_return=10.0,
            annual_return=5.0,
            sharpe_ratio=1.0,
            sortino_ratio=1.2,
            max_drawdown=5.0,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.6,
            profit_factor=1.5,
            expectancy=100.0,
            score=1.0,
            beats_bnh=5.0,
            metric_type="Most Sharpe Ratio, Most Sortino Ratio",
        )

        data = portfolio.model_dump()
        assert "metric_type" in data
        assert data["metric_type"] == "Most Sharpe Ratio, Most Sortino Ratio"

    def test_model_dump_exclude_none_false(self):
        """Test that model_dump(exclude_none=False) includes empty metric_type."""
        portfolio = PortfolioMetrics(
            ticker="TEST",
            strategy_type="SMA",
            short_window=5,
            long_window=10,
            total_return=10.0,
            annual_return=5.0,
            sharpe_ratio=1.0,
            sortino_ratio=1.2,
            max_drawdown=5.0,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.6,
            profit_factor=1.5,
            expectancy=100.0,
            score=1.0,
            beats_bnh=5.0,
            # metric_type defaults to ""
        )

        data = portfolio.model_dump(exclude_none=False)
        assert "metric_type" in data
        assert data["metric_type"] == ""

    def test_complex_metric_type_values(self):
        """Test various complex metric_type values."""
        test_cases = [
            "Most Total Return [%]",
            "Most Sharpe Ratio, Most Sortino Ratio",
            "Most Omega Ratio, Most Sharpe Ratio, Most Sortino Ratio, Most Total Return [%], Median Total Trades",
            "Mean Avg Winning Trade [%]",
            "",
            "Special-Characters: Test_Value [100%]",
        ]

        for metric_type_value in test_cases:
            portfolio = PortfolioMetrics(
                ticker="TEST",
                strategy_type="SMA",
                short_window=5,
                long_window=10,
                total_return=10.0,
                annual_return=5.0,
                sharpe_ratio=1.0,
                sortino_ratio=1.2,
                max_drawdown=5.0,
                total_trades=10,
                winning_trades=6,
                losing_trades=4,
                win_rate=0.6,
                profit_factor=1.5,
                expectancy=100.0,
                score=1.0,
                beats_bnh=5.0,
                metric_type=metric_type_value,
            )

            assert portfolio.metric_type == metric_type_value

            # Test serialization preserves the value
            data = portfolio.model_dump()
            assert data["metric_type"] == metric_type_value

    def test_from_dict_with_metric_type(self):
        """Test creating PortfolioMetrics from dictionary with metric_type."""
        portfolio_dict = {
            "ticker": "TEST",
            "strategy_type": "EMA",
            "short_window": 12,
            "long_window": 26,
            "total_return": 25.0,
            "annual_return": 8.0,
            "sharpe_ratio": 1.5,
            "sortino_ratio": 1.8,
            "max_drawdown": 10.0,
            "total_trades": 15,
            "winning_trades": 9,
            "losing_trades": 6,
            "win_rate": 0.6,
            "profit_factor": 2.0,
            "expectancy": 150.0,
            "score": 1.2,
            "beats_bnh": 10.0,
            "has_open_trade": True,
            "has_signal_entry": False,
            "metric_type": "Most Omega Ratio",
        }

        portfolio = PortfolioMetrics(**portfolio_dict)
        assert portfolio.metric_type == "Most Omega Ratio"

        # Test round-trip serialization
        serialized = portfolio.model_dump()
        reconstructed = PortfolioMetrics(**serialized)
        assert reconstructed.metric_type == "Most Omega Ratio"

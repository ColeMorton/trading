"""
Test Phase 2 Service Decomposition

Tests for the decomposed services: ParameterTestingService, PortfolioFilterService,
ResultsExportService, and MACrossOrchestrator.
"""

from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from app.api.services.ma_cross_orchestrator import MACrossOrchestrator
from app.api.services.parameter_testing_service import ParameterTestingService
from app.api.services.portfolio_filter_service import PortfolioFilterService
from app.api.services.results_export_service import ResultsExportService


class TestParameterTestingService:
    """Test suite for ParameterTestingService."""

    @pytest.fixture
    def service(self):
        """Create ParameterTestingService with mocked dependencies."""
        return ParameterTestingService(
            logger=Mock(),
            progress_tracker=Mock(),
            strategy_executor=Mock(),
        )

    @pytest.fixture
    def basic_config(self):
        """Basic configuration for testing."""
        return {
            "TICKER": ["AAPL", "GOOGL", "MSFT"],
            "WINDOWS": 20,
            "STRATEGY_TYPES": ["SMA", "EMA"],
            "DIRECTION": "Long",
            "BASE_DIR": "/Users/colemorton/Projects/trading",
        }

    def test_validate_parameters_valid(self, service):
        """Test parameter validation with valid inputs."""
        is_valid, error = service.validate_parameters(
            tickers=["AAPL", "GOOGL"],
            windows=20,
            strategy_types=["SMA", "EMA"],
        )

        assert is_valid is True
        assert error is None

    def test_validate_parameters_invalid_tickers(self, service):
        """Test parameter validation with invalid tickers."""
        is_valid, error = service.validate_parameters(
            tickers=[],
            windows=20,
            strategy_types=["SMA"],
        )

        assert is_valid is False
        assert "No tickers provided" in error

    def test_validate_parameters_invalid_windows(self, service):
        """Test parameter validation with invalid windows."""
        is_valid, error = service.validate_parameters(
            tickers=["AAPL"],
            windows=1,
            strategy_types=["SMA"],
        )

        assert is_valid is False
        assert "Windows must be an integer >= 2" in error

    def test_validate_parameters_invalid_strategies(self, service):
        """Test parameter validation with invalid strategy types."""
        is_valid, error = service.validate_parameters(
            tickers=["AAPL"],
            windows=20,
            strategy_types=["INVALID"],
        )

        assert is_valid is False
        assert "Invalid strategy types" in error

    def test_estimate_execution_time(self, service):
        """Test execution time estimation."""
        estimated_time = service.estimate_execution_time(
            ticker_count=5,
            window_size=20,
            strategy_count=2,
        )

        assert isinstance(estimated_time, float)
        assert estimated_time > 0

    def test_estimate_execution_time_concurrent(self, service):
        """Test execution time estimation with concurrent execution."""
        # 3+ tickers should use concurrent execution (faster)
        concurrent_time = service.estimate_execution_time(
            ticker_count=5,
            window_size=20,
            strategy_count=2,
        )

        # 2 tickers should use sequential execution (slower)
        sequential_time = service.estimate_execution_time(
            ticker_count=2,
            window_size=20,
            strategy_count=2,
        )

        assert concurrent_time < sequential_time

    @patch("app.api.services.parameter_testing_service.execute_strategy_concurrent")
    @patch("app.api.services.parameter_testing_service.ConfigService.process_config")
    def test_execute_parameter_sweep_concurrent(
        self, mock_process_config, mock_execute_concurrent, service, basic_config
    ):
        """Test parameter sweep execution using concurrent method."""
        mock_process_config.return_value = basic_config
        mock_execute_concurrent.return_value = [
            {"Ticker": "AAPL", "Strategy Type": "SMA", "Total Return [%]": 15.0},
            {"Ticker": "GOOGL", "Strategy Type": "SMA", "Total Return [%]": 12.0},
        ]

        portfolios, execution_time = service.execute_parameter_sweep(
            basic_config,
            ["SMA", "EMA"],
        )

        assert len(portfolios) > 0
        assert execution_time > 0
        # Should use concurrent for 3+ tickers
        assert mock_execute_concurrent.call_count == 2  # Called for each strategy


class TestPortfolioFilterService:
    """Test suite for PortfolioFilterService."""

    @pytest.fixture
    def service(self):
        """Create PortfolioFilterService with mocked dependencies."""
        return PortfolioFilterService(logger=Mock())

    @pytest.fixture
    def sample_portfolios(self):
        """Sample portfolio data for testing."""
        return [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Total Return [%]": 15.5,
                "Win Rate [%]": 65.0,
                "Total Trades": 25,
                "Profit Factor": 1.8,
                "Sortino Ratio": 1.2,
                "Score": 85.0,
                "Sharpe Ratio": 1.1,
            },
            {
                "Ticker": "GOOGL",
                "Strategy Type": "EMA",
                "Total Return [%]": 8.2,
                "Win Rate [%]": 45.0,
                "Total Trades": 15,
                "Profit Factor": 1.1,
                "Sortino Ratio": 0.8,
                "Score": 60.0,
                "Sharpe Ratio": 0.9,
            },
            {
                "Ticker": "MSFT",
                "Strategy Type": "SMA",
                "Total Return [%]": 22.1,
                "Win Rate [%]": 72.0,
                "Total Trades": 30,
                "Profit Factor": 2.2,
                "Sortino Ratio": 1.5,
                "Score": 95.0,
                "Sharpe Ratio": 1.4,
            },
        ]

    def test_filter_portfolios_no_filters(self, service, sample_portfolios):
        """Test filtering with no criteria (should return all)."""
        filtered = service.filter_portfolios(sample_portfolios, {})
        assert len(filtered) == len(sample_portfolios)

    def test_filter_portfolios_win_rate_filter(self, service, sample_portfolios):
        """Test filtering by win rate."""
        criteria = {"minimums": {"win_rate": 0.6}}  # 60%
        filtered = service.filter_portfolios(sample_portfolios, criteria)

        # Should filter out GOOGL (45% win rate)
        assert len(filtered) == 2
        tickers = [p["Ticker"] for p in filtered]
        assert "AAPL" in tickers
        assert "MSFT" in tickers
        assert "GOOGL" not in tickers

    def test_filter_portfolios_multiple_filters(self, service, sample_portfolios):
        """Test filtering with multiple criteria."""
        criteria = {
            "minimums": {
                "win_rate": 0.6,
                "trades": 20,
                "profit_factor": 1.5,
            }
        }
        filtered = service.filter_portfolios(sample_portfolios, criteria)

        # Should keep AAPL (1.8 PF, 25 trades, 65% WR) and MSFT (2.2 PF, 30 trades, 72% WR)
        # Should filter out GOOGL (1.1 PF < 1.5, 15 trades < 20, 45% WR < 60%)
        assert len(filtered) == 2
        tickers = [p["Ticker"] for p in filtered]
        assert "AAPL" in tickers
        assert "MSFT" in tickers
        assert "GOOGL" not in tickers

    def test_get_best_portfolios_by_metric(self, service, sample_portfolios):
        """Test getting best portfolios by specific metric."""
        best = service.get_best_portfolios_by_metric(
            sample_portfolios,
            "Total Return [%]",
            top_n=2,
        )

        assert len(best) == 2
        # Should be sorted by Total Return descending
        assert best[0]["Ticker"] == "MSFT"  # 22.1%
        assert best[1]["Ticker"] == "AAPL"  # 15.5%

    def test_group_portfolios_by_ticker(self, service, sample_portfolios):
        """Test grouping portfolios by ticker."""
        grouped = service.group_portfolios_by_ticker(sample_portfolios)

        assert len(grouped) == 3
        assert "AAPL" in grouped
        assert "GOOGL" in grouped
        assert "MSFT" in grouped
        assert len(grouped["AAPL"]) == 1

    def test_get_filter_statistics(self, service, sample_portfolios):
        """Test filter statistics generation."""
        filtered = sample_portfolios[:2]  # Remove one portfolio
        stats = service.get_filter_statistics(sample_portfolios, filtered)

        assert stats["original_count"] == 3
        assert stats["filtered_count"] == 2
        assert stats["removed_count"] == 1
        assert stats["retention_rate"] == 2 / 3


class TestResultsExportService:
    """Test suite for ResultsExportService."""

    @pytest.fixture
    def service(self):
        """Create ResultsExportService with mocked dependencies."""
        return ResultsExportService(logger=Mock())

    @pytest.fixture
    def sample_portfolio_dicts(self):
        """Sample portfolio dictionaries for testing."""
        return [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "SMA_FAST": 5,
                "SMA_SLOW": 20,
                "Total Return [%]": 15.5,
                "Win Rate [%]": 65.0,
                "Total Trades": 25,
                "Total Open Trades": 1,
                "Signal Entry": True,
                "Metric Type": "Most Total Return [%]",
            },
        ]

    def test_convert_to_portfolio_metrics(self, service, sample_portfolio_dicts):
        """Test conversion from dictionaries to PortfolioMetrics."""
        metrics = service.convert_to_portfolio_metrics(sample_portfolio_dicts)

        assert len(metrics) == 1
        metric = metrics[0]
        assert metric.ticker == "AAPL"
        assert metric.strategy_type == "SMA"
        assert metric.short_window == 5
        assert metric.long_window == 20
        assert metric.win_rate == 0.65  # Converted from percentage
        assert metric.has_open_trade is True
        assert metric.has_signal_entry is True

    def test_convert_handles_enum_prefix(self, service):
        """Test conversion handles StrategyTypeEnum prefix."""
        portfolio_dicts = [
            {
                "Ticker": "MSFT",
                "Strategy Type": "StrategyTypeEnum.SMA",
                "SMA_FAST": 10,
                "SMA_SLOW": 30,
                "Total Return [%]": 12.0,
                "Win Rate [%]": 60.0,
                "Total Trades": 20,
                "Metric Type": "Test Type",
            }
        ]

        metrics = service.convert_to_portfolio_metrics(portfolio_dicts)
        assert metrics[0].strategy_type == "SMA"  # Enum prefix removed

    def test_create_summary_report(self, service, sample_portfolio_dicts):
        """Test summary report creation."""
        summary = service.create_summary_report(sample_portfolio_dicts, 1.234)

        assert summary["total_portfolios"] == 1
        assert summary["execution_time"] == 1.23  # Rounded
        assert "performance_summary" in summary
        assert "strategy_distribution" in summary

    def test_create_summary_report_empty(self, service):
        """Test summary report with empty portfolios."""
        summary = service.create_summary_report([], 0.5)

        assert summary["total_portfolios"] == 0
        assert summary["execution_time"] == 0.5
        assert summary["summary"] == "No portfolios generated"

    def test_aggregate_results_by_ticker(self, service):
        """Test result aggregation by ticker."""
        portfolios = [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Total Return [%]": 15.0,
                "Sharpe Ratio": 1.2,
            },
            {
                "Ticker": "AAPL",
                "Strategy Type": "EMA",
                "Total Return [%]": 12.0,
                "Sharpe Ratio": 1.0,
            },
            {
                "Ticker": "GOOGL",
                "Strategy Type": "SMA",
                "Total Return [%]": 18.0,
                "Sharpe Ratio": 1.5,
            },
        ]

        aggregated = service.aggregate_results_by_ticker(portfolios)

        assert len(aggregated) == 2
        assert aggregated["AAPL"]["portfolio_count"] == 2
        assert aggregated["AAPL"]["best_return"] == 15.0
        assert "SMA" in aggregated["AAPL"]["strategies"]
        assert "EMA" in aggregated["AAPL"]["strategies"]


class TestMACrossOrchestrator:
    """Test suite for MACrossOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create MACrossOrchestrator with mocked dependencies."""
        return MACrossOrchestrator(
            logger=Mock(),
            progress_tracker=Mock(),
            strategy_executor=Mock(),
            strategy_analyzer=Mock(),
            cache=Mock(),
            monitoring=Mock(),
            configuration=Mock(),
        )

    def test_generate_cache_key(self, orchestrator):
        """Test cache key generation."""
        from app.api.models.strategy_analysis import MACrossRequest, MinimumCriteria

        request = MACrossRequest(
            ticker=["AAPL", "GOOGL"],
            windows=20,
            strategy_types=["SMA", "EMA"],
            direction="Long",
            use_hourly=False,
            minimums=MinimumCriteria(win_rate=0.6, trades=10),
        )

        cache_key = orchestrator._generate_cache_key(request)

        assert "ma_cross:v2" in cache_key
        assert "t:AAPL,GOOGL" in cache_key  # Sorted tickers
        assert "w:20" in cache_key
        assert "s:EMA,SMA" in cache_key  # Sorted strategies
        assert "min:wr:0.6-tr:10" in cache_key

    def test_create_config_from_request(self, orchestrator):
        """Test configuration creation from request."""
        from app.api.models.strategy_analysis import MACrossRequest

        request = MACrossRequest(
            ticker=["AAPL", "GOOGL"],
            windows=20,
            strategy_types=["SMA"],
            direction="Long",
            use_hourly=False,
            use_years=True,
            years=5,
        )

        config = orchestrator._create_config_from_request(request)

        assert config["TICKER"] == ["AAPL", "GOOGL"]
        assert config["WINDOWS"] == 20
        assert config["STRATEGY_TYPES"] == ["SMA"]
        assert config["DIRECTION"] == "Long"
        assert config["USE_HOURLY"] is False
        assert config["USE_YEARS"] is True
        assert config["YEARS"] == 5

    def test_create_filter_criteria(self, orchestrator):
        """Test filter criteria creation from request."""
        from app.api.models.strategy_analysis import MACrossRequest, MinimumCriteria

        request = MACrossRequest(
            ticker="AAPL",
            windows=20,
            strategy_types=["SMA"],
            minimums=MinimumCriteria(
                win_rate=0.6,
                trades=10,
                profit_factor=1.5,
            ),
        )

        criteria = orchestrator._create_filter_criteria(request)

        assert criteria["minimums"]["win_rate"] == 0.6
        assert criteria["minimums"]["trades"] == 10
        assert criteria["minimums"]["profit_factor"] == 1.5

    def test_map_sort_field(self, orchestrator):
        """Test sort field mapping."""
        assert orchestrator._map_sort_field("total_return") == "Total Return [%]"
        assert orchestrator._map_sort_field("win_rate") == "Win Rate [%]"
        assert orchestrator._map_sort_field("custom_field") == "custom_field"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

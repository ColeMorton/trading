"""
Performance Benchmarks for MA Cross Module

This module provides performance testing and benchmarking for the MA Cross
strategy analysis system to ensure optimal performance characteristics.
"""

import os
import tempfile
import time
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import polars as pl
import psutil
import pytest

from app.tools.orchestration.portfolio_orchestrator import PortfolioOrchestrator


class TestMACrossPerformanceBenchmarks:
    """Performance benchmarks for MA Cross operations."""

    @pytest.fixture
    def mock_log(self):
        """Mock logging function."""
        return Mock()

    @pytest.fixture
    def performance_config(self):
        """Configuration optimized for performance testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield {
                "TICKER": ["BTC-USD"],
                "STRATEGY_TYPE": "SMA",
                "FAST_PERIOD": 10,
                "SLOW_PERIOD": 20,
                "WINDOWS": [[5, 10], [10, 20], [15, 30]],
                "DIRECTION": "BOTH",
                "TIMEFRAME": "D",
                "PORTFOLIO_DIR": temp_dir,
                "PORTFOLIO_FILTERED_DIR": temp_dir,
                "STRATEGY_DIR": temp_dir,
                "USE_MA": True,
                "USE_SYNTHETIC": False,
                "ALLOCATION": 100,
                "STOP_LOSS": 5.0,
            }

    @pytest.fixture
    def large_price_dataset(self):
        """Generate large price dataset for performance testing."""
        np.random.seed(42)

        # Generate 5 years of daily data (1825 days)
        dates = pd.date_range("2019-01-01", periods=1825, freq="D")

        # Generate realistic price series with volatility
        base_price = 40000
        returns = np.random.normal(0.0005, 0.025, 1825)
        prices = [base_price]

        for ret in returns[1:]:
            prices.append(max(prices[-1] * (1 + ret), 1000))  # Prevent negative prices

        df = pd.DataFrame(
            {
                "Date": dates,
                "Open": prices,
                "High": [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                "Low": [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                "Close": prices,
                "Volume": np.random.randint(1000000, 50000000, 1825),
            }
        )

        return pl.from_pandas(df)

    @pytest.fixture
    def large_portfolio_dataset(self):
        """Generate large portfolio dataset for performance testing."""
        strategies = []

        # Generate 100 strategy combinations
        for sma_fast in range(5, 25, 2):
            for sma_slow in range(26, 51, 3):
                if sma_fast < sma_slow:
                    strategies.append(
                        {
                            "TICKER": "BTC-USD",
                            "Strategy Type": "SMA",
                            "SMA_FAST": sma_fast,
                            "SMA_SLOW": sma_slow,
                            "Total Return [%]": np.random.uniform(5, 25),
                            "Annual Return [%]": np.random.uniform(3, 18),
                            "Volatility [%]": np.random.uniform(15, 35),
                            "Sharpe Ratio": np.random.uniform(0.3, 1.2),
                            "Max Drawdown [%]": np.random.uniform(-25, -5),
                            "Win Rate [%]": np.random.uniform(45, 75),
                            "Profit Factor": np.random.uniform(1.1, 2.0),
                            "Num Trades": np.random.randint(10, 100),
                            "Current Signal": np.random.choice([True, False]),
                            "Exit Signal": np.random.choice([True, False]),
                            "Allocation [%]": 100,
                            "Stop Loss [%]": 5.0,
                        }
                    )

        return strategies


class TestSingleOperationBenchmarks(TestMACrossPerformanceBenchmarks):
    """Benchmark individual operations."""

    def test_config_processing_performance(self, performance_config, mock_log):
        """Benchmark configuration processing performance."""
        from app.tools.config_service import ConfigService

        start_time = time.time()

        # Process config multiple times
        for _ in range(1000):
            processed_config = ConfigService.process_config(performance_config)

        execution_time = time.time() - start_time

        # Should process 1000 configs in under 1 second
        assert execution_time < 1.0
        assert processed_config is not None

    def test_strategy_creation_performance(self, mock_log):
        """Benchmark strategy creation performance."""
        from app.tools.strategy.factory import StrategyFactory

        factory = StrategyFactory()
        start_time = time.time()

        # Create strategies multiple times
        for _ in range(1000):
            factory.create_strategy("SMA")
            factory.create_strategy("EMA")

        execution_time = time.time() - start_time

        # Should create 2000 strategies in under 0.5 seconds
        assert execution_time < 0.5

    def test_portfolio_filtering_performance(
        self, large_portfolio_dataset, performance_config, mock_log
    ):
        """Benchmark portfolio filtering performance."""
        from app.tools.portfolio.filtering_service import PortfolioFilterService

        filter_service = PortfolioFilterService()
        portfolios_df = pl.DataFrame(large_portfolio_dataset)

        start_time = time.time()

        # Filter portfolios multiple times
        for _ in range(100):
            filtered_df = filter_service.filter_portfolios_dataframe(
                portfolios_df, performance_config, mock_log
            )

        execution_time = time.time() - start_time

        # Should filter 100 times in under 2 seconds
        assert execution_time < 2.0
        assert filtered_df is not None


class TestWorkflowBenchmarks(TestMACrossPerformanceBenchmarks):
    """Benchmark complete workflow operations."""

    def test_single_ticker_workflow_benchmark(
        self, performance_config, large_price_dataset, large_portfolio_dataset, mock_log
    ):
        """Benchmark single ticker complete workflow."""

        with (
            patch("app.tools.get_data.get_data") as mock_get_data,
            patch(
                "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
            ) as mock_process,
            patch(
                "app.tools.portfolio.filtering_service.PortfolioFilterService"
            ) as mock_filter_service,
            patch("app.tools.strategy.export_portfolios.export_portfolios"),
        ):
            # Setup mocks with large dataset
            mock_get_data.return_value = large_price_dataset
            mock_process.return_value = pl.DataFrame(large_portfolio_dataset)

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.return_value = (
                pl.DataFrame(large_portfolio_dataset[:10])
            )
            mock_filter_service.return_value = mock_filter_instance

            # Benchmark workflow execution
            orchestrator = PortfolioOrchestrator(mock_log)

            start_time = time.time()
            result = orchestrator.run(performance_config)
            execution_time = time.time() - start_time

            # Should complete single ticker workflow in under 3 seconds
            assert execution_time < 3.0
            assert result is not None

    def test_multiple_ticker_workflow_benchmark(
        self, performance_config, large_price_dataset, large_portfolio_dataset, mock_log
    ):
        """Benchmark multiple ticker workflow."""

        # Configure for 5 tickers
        multi_config = performance_config.copy()
        multi_config["TICKER"] = ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "DOT-USD"]

        with (
            patch("app.tools.get_data.get_data") as mock_get_data,
            patch(
                "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
            ) as mock_process,
            patch(
                "app.tools.portfolio.filtering_service.PortfolioFilterService"
            ) as mock_filter_service,
            patch("app.tools.strategy.export_portfolios.export_portfolios"),
        ):
            # Setup mocks
            mock_get_data.return_value = large_price_dataset
            mock_process.return_value = pl.DataFrame(large_portfolio_dataset)

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.return_value = (
                pl.DataFrame(large_portfolio_dataset[:10])
            )
            mock_filter_service.return_value = mock_filter_instance

            # Benchmark workflow execution
            orchestrator = PortfolioOrchestrator(mock_log)

            start_time = time.time()
            result = orchestrator.run(multi_config)
            execution_time = time.time() - start_time

            # Should complete 5-ticker workflow in under 10 seconds
            assert execution_time < 10.0
            assert result is not None

    def test_multi_strategy_workflow_benchmark(
        self, performance_config, large_price_dataset, large_portfolio_dataset, mock_log
    ):
        """Benchmark multiple strategy workflow."""

        # Configure for multiple strategies
        multi_strategy_config = performance_config.copy()
        multi_strategy_config["STRATEGY_TYPE"] = ["SMA", "EMA"]

        with (
            patch("app.tools.get_data.get_data") as mock_get_data,
            patch(
                "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
            ) as mock_process,
            patch(
                "app.tools.portfolio.filtering_service.PortfolioFilterService"
            ) as mock_filter_service,
            patch("app.tools.strategy.export_portfolios.export_portfolios"),
        ):
            # Setup mocks
            mock_get_data.return_value = large_price_dataset
            mock_process.return_value = pl.DataFrame(large_portfolio_dataset)

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.return_value = (
                pl.DataFrame(large_portfolio_dataset[:10])
            )
            mock_filter_service.return_value = mock_filter_instance

            # Benchmark workflow execution
            orchestrator = PortfolioOrchestrator(mock_log)

            start_time = time.time()
            result = orchestrator.run(multi_strategy_config)
            execution_time = time.time() - start_time

            # Should complete multi-strategy workflow in under 8 seconds
            assert execution_time < 8.0
            assert result is not None


class TestMemoryBenchmarks(TestMACrossPerformanceBenchmarks):
    """Benchmark memory usage patterns."""

    def test_workflow_memory_usage(
        self, performance_config, large_price_dataset, large_portfolio_dataset, mock_log
    ):
        """Test memory usage during workflow execution."""

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        with (
            patch("app.tools.get_data.get_data") as mock_get_data,
            patch(
                "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
            ) as mock_process,
            patch(
                "app.tools.portfolio.filtering_service.PortfolioFilterService"
            ) as mock_filter_service,
        ):
            # Setup mocks with large datasets
            mock_get_data.return_value = large_price_dataset
            mock_process.return_value = pl.DataFrame(large_portfolio_dataset)

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.return_value = (
                pl.DataFrame(large_portfolio_dataset[:10])
            )
            mock_filter_service.return_value = mock_filter_instance

            # Execute workflow and monitor memory
            orchestrator = PortfolioOrchestrator(mock_log)
            result = orchestrator.run(performance_config)

            peak_memory = process.memory_info().rss
            memory_increase = peak_memory - initial_memory

            # Memory increase should be reasonable (less than 200MB)
            assert memory_increase < 200 * 1024 * 1024  # 200MB
            assert result is not None

    def test_memory_cleanup(
        self, performance_config, large_price_dataset, large_portfolio_dataset, mock_log
    ):
        """Test memory cleanup after workflow execution."""

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        with (
            patch("app.tools.get_data.get_data") as mock_get_data,
            patch(
                "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
            ) as mock_process,
            patch(
                "app.tools.portfolio.filtering_service.PortfolioFilterService"
            ) as mock_filter_service,
        ):
            # Setup mocks
            mock_get_data.return_value = large_price_dataset
            mock_process.return_value = pl.DataFrame(large_portfolio_dataset)

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.return_value = (
                pl.DataFrame(large_portfolio_dataset[:10])
            )
            mock_filter_service.return_value = mock_filter_instance

            # Execute workflow multiple times
            orchestrator = PortfolioOrchestrator(mock_log)
            for _ in range(5):
                result = orchestrator.run(performance_config)
                assert result is not None

            # Force garbage collection
            import gc

            gc.collect()

            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Memory should not grow significantly after multiple runs
            assert memory_increase < 50 * 1024 * 1024  # 50MB


class TestConcurrencyBenchmarks(TestMACrossPerformanceBenchmarks):
    """Benchmark concurrency and parallelization."""

    def test_concurrent_ticker_processing(
        self, performance_config, large_price_dataset, large_portfolio_dataset, mock_log
    ):
        """Test concurrent processing of multiple tickers."""
        import concurrent.futures

        # Configure for concurrent processing
        concurrent_config = performance_config.copy()
        tickers = ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "DOT-USD"]

        with (
            patch("app.tools.get_data.get_data") as mock_get_data,
            patch(
                "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
            ) as mock_process,
            patch(
                "app.tools.portfolio.filtering_service.PortfolioFilterService"
            ) as mock_filter_service,
        ):
            # Setup mocks
            mock_get_data.return_value = large_price_dataset
            mock_process.return_value = pl.DataFrame(large_portfolio_dataset)

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.return_value = (
                pl.DataFrame(large_portfolio_dataset[:10])
            )
            mock_filter_service.return_value = mock_filter_instance

            def process_ticker(ticker):
                ticker_config = concurrent_config.copy()
                ticker_config["TICKER"] = [ticker]
                orchestrator = PortfolioOrchestrator(mock_log)
                return orchestrator.run(ticker_config)

            # Benchmark sequential vs concurrent processing
            start_time = time.time()
            sequential_results = [process_ticker(ticker) for ticker in tickers]
            sequential_time = time.time() - start_time

            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                concurrent_results = list(executor.map(process_ticker, tickers))
            concurrent_time = time.time() - start_time

            # Concurrent processing should be faster (allowing for overhead)
            assert len(sequential_results) == len(concurrent_results) == len(tickers)
            assert all(r is not None for r in sequential_results)
            assert all(r is not None for r in concurrent_results)

            # Note: Concurrent may not always be faster due to mocking overhead,
            # but it should not be significantly slower
            assert concurrent_time < sequential_time * 1.5


class TestScalabilityBenchmarks(TestMACrossPerformanceBenchmarks):
    """Test scalability with increasing data sizes."""

    @pytest.mark.parametrize("num_portfolios", [10, 50, 100, 200])
    def test_filtering_scalability(self, performance_config, mock_log, num_portfolios):
        """Test filtering performance with increasing portfolio counts."""
        from app.tools.portfolio.filtering_service import PortfolioFilterService

        # Generate portfolios of different sizes
        portfolios = []
        for i in range(num_portfolios):
            portfolios.append(
                {
                    "TICKER": "BTC-USD",
                    "Strategy Type": "SMA",
                    "SMA_FAST": 5 + i % 20,
                    "SMA_SLOW": 25 + i % 25,
                    "Total Return [%]": np.random.uniform(5, 25),
                    "Sharpe Ratio": np.random.uniform(0.3, 1.2),
                    "Allocation [%]": 100,
                    "Stop Loss [%]": 5.0,
                }
            )

        filter_service = PortfolioFilterService()
        portfolios_df = pl.DataFrame(portfolios)

        start_time = time.time()
        filtered_df = filter_service.filter_portfolios_dataframe(
            portfolios_df, performance_config, mock_log
        )
        execution_time = time.time() - start_time

        # Execution time should scale reasonably (linear or better)
        max_expected_time = num_portfolios * 0.001  # 1ms per portfolio max
        assert execution_time < max_expected_time
        assert filtered_df is not None

    @pytest.mark.parametrize("data_points", [100, 500, 1000, 2000])
    def test_data_processing_scalability(
        self, performance_config, mock_log, data_points
    ):
        """Test data processing performance with increasing data sizes."""

        # Generate price data of different sizes
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=data_points, freq="D")
        prices = np.random.uniform(40000, 60000, data_points)

        df = pd.DataFrame(
            {
                "Date": dates,
                "Open": prices,
                "High": prices * 1.02,
                "Low": prices * 0.98,
                "Close": prices,
                "Volume": np.random.randint(1000000, 10000000, data_points),
            }
        )

        price_data = pl.from_pandas(df)

        with (
            patch("app.tools.get_data.get_data") as mock_get_data,
            patch(
                "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
            ) as mock_process,
            patch(
                "app.tools.portfolio.filtering_service.PortfolioFilterService"
            ) as mock_filter_service,
        ):
            # Setup mocks
            mock_get_data.return_value = price_data
            mock_process.return_value = pl.DataFrame(
                [
                    {
                        "TICKER": "BTC-USD",
                        "Strategy Type": "SMA",
                        "SMA_FAST": 10,
                        "SMA_SLOW": 20,
                        "Total Return [%]": 15.5,
                        "Allocation [%]": 100,
                        "Stop Loss [%]": 5.0,
                    }
                ]
            )

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.return_value = (
                pl.DataFrame(
                    [
                        {
                            "TICKER": "BTC-USD",
                            "Strategy Type": "SMA",
                            "Total Return [%]": 15.5,
                        }
                    ]
                )
            )
            mock_filter_service.return_value = mock_filter_instance

            # Benchmark data processing
            orchestrator = PortfolioOrchestrator(mock_log)

            start_time = time.time()
            result = orchestrator.run(performance_config)
            execution_time = time.time() - start_time

            # Execution time should scale reasonably with data size
            max_expected_time = data_points * 0.002  # 2ms per data point max
            assert execution_time < max_expected_time
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

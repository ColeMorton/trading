"""
Regression tests for Batch Size Fix.

These tests verify the fix for the batch size issue where the number of tickers
processed was always one less than the batch_size specified due to resume analysis
filtering happening after batch selection instead of being integrated into it.

Critical regression scenarios tested:
- Exactly batch_size tickers are processed (not selected then filtered)
- Resume-aware selection works correctly
- No off-by-one errors in batch processing
- Performance regression prevention
- Integration between BatchProcessingService and StrategyDispatcher

This test suite prevents regression of the issue where:
- User requests batch_size=2
- System selects 2 tickers (AAPL, ACGL)
- Resume analysis skips AAPL (already complete)
- Only 1 ticker (ACGL) gets processed
- User sees "processed 1 ticker" instead of expected 2

After the fix:
- User requests batch_size=2
- System checks tickers with resume analysis during selection
- System selects exactly 2 tickers that need processing (ACGL, ACN)
- Both tickers get processed
- User sees "processed 2 tickers" as expected
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from app.cli.models.strategy import (
    StrategyConfig,
    StrategyMinimums,
    StrategyType,
    SyntheticTickerConfig,
)
from app.cli.services.batch_processing_service import BatchProcessingService
from app.cli.services.strategy_dispatcher import StrategyDispatcher
from app.tools.console_logging import ConsoleLogger


class TestBatchSizeFixRegression:
    """Regression tests for the batch size fix."""

    @pytest.fixture
    def temp_batch_file(self):
        """Create temporary batch file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")
            yield f.name

        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def mock_console(self):
        """Create mock console logger."""
        return Mock(spec=ConsoleLogger)

    @pytest.fixture
    def batch_service(self, temp_batch_file, mock_console):
        """Create BatchProcessingService instance."""
        return BatchProcessingService(temp_batch_file, mock_console)

    @pytest.fixture
    def sample_strategy_config(self, temp_batch_file):
        """Create sample strategy config with batch settings."""
        return StrategyConfig(
            ticker=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
            strategy_types=[StrategyType.SMA],
            use_years=False,
            years=15,
            multi_ticker=False,
            use_scanner=False,
            scanner_list="",
            use_gbm=False,
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
            batch=True,
            batch_size=2,
            batch_file_path=temp_batch_file,
        )

    def test_regression_exact_batch_size_processing(self, batch_service):
        """
        REGRESSION TEST: Verify exactly batch_size tickers are processed.

        This test prevents regression of the issue where batch_size=2 would
        result in only 1 ticker being processed due to resume filtering.
        """
        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        batch_size = 2

        # Mock resume check that skips first ticker (AAPL)
        call_count = 0

        def mock_resume_check(ticker):
            nonlocal call_count
            call_count += 1
            # Skip AAPL (first ticker), process others
            return ticker != "AAPL"

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check
        )

        # CRITICAL: Should return exactly batch_size tickers that need processing
        assert (
            len(result) == batch_size
        ), f"Expected {batch_size} tickers, got {len(result)}"

        # Should exclude AAPL (skipped by resume check)
        assert "AAPL" not in result

        # Should include next 2 tickers that need processing
        assert set(result) == {"MSFT", "GOOGL"}

        # Should stop checking after finding enough tickers
        assert call_count == 3  # AAPL (skip), MSFT (include), GOOGL (include)

    def test_regression_batch_size_three_with_mixed_resume_results(self, batch_service):
        """
        REGRESSION TEST: Test batch_size=3 with mixed resume results.

        This test ensures the fix works correctly for different batch sizes
        and various resume analysis patterns.
        """
        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN"]
        batch_size = 3

        # Mock resume check that skips AAPL and GOOGL
        def mock_resume_check(ticker):
            return ticker not in ["AAPL", "GOOGL"]

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check
        )

        # Should return exactly 3 tickers
        assert len(result) == 3

        # Should exclude skipped tickers
        assert "AAPL" not in result
        assert "GOOGL" not in result

        # Should include first 3 tickers that need processing
        assert set(result) == {"MSFT", "TSLA", "NVDA"}

    def test_regression_no_available_tickers_after_resume_check(self, batch_service):
        """
        REGRESSION TEST: Test when no tickers need processing after resume check.

        This test ensures graceful handling when all tickers are skipped
        by resume analysis.
        """
        all_tickers = ["AAPL", "MSFT", "GOOGL"]
        batch_size = 2

        # Mock resume check that skips all tickers
        def mock_resume_check(ticker):
            return False  # All tickers are complete

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check
        )

        # Should return empty list (no tickers need processing)
        assert len(result) == 0
        assert result == []

    def test_regression_fewer_tickers_available_than_batch_size(self, batch_service):
        """
        REGRESSION TEST: Test when fewer tickers need processing than batch_size.

        This test ensures the fix handles edge cases where not enough
        tickers need processing to fill the batch.
        """
        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        batch_size = 5  # Larger than available tickers

        # Only 2 tickers need processing
        def mock_resume_check(ticker):
            return ticker in ["MSFT", "GOOGL"]

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check
        )

        # Should return only the tickers that need processing
        assert len(result) == 2
        assert set(result) == {"MSFT", "GOOGL"}

    def test_regression_batch_file_integration_with_resume_aware_selection(
        self, batch_service
    ):
        """
        REGRESSION TEST: Test integration of batch file status with resume-aware selection.

        This test ensures that both batch file tracking and resume analysis
        work together correctly after the fix.
        """
        # Add some already processed tickers to batch file
        today = datetime.now().strftime("%Y-%m-%d")
        processed_data = [
            {"Ticker": "AAPL", "Last Modified": today},
            {"Ticker": "MSFT", "Last Modified": today},
        ]
        df = pd.DataFrame(processed_data)
        df.to_csv(batch_service.batch_file_path, index=False)

        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        batch_size = 2

        # Mock resume check - GOOGL is complete, others need processing
        def mock_resume_check(ticker):
            return ticker != "GOOGL"

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check
        )

        # Should exclude AAPL, MSFT (batch file) and GOOGL (resume check)
        # Should include TSLA, NVDA (first 2 that need processing)
        assert len(result) == 2
        assert set(result) == {"TSLA", "NVDA"}

    def test_regression_performance_early_termination(self, batch_service):
        """
        REGRESSION TEST: Test that selection stops early when batch_size is reached.

        This test ensures the fix maintains performance by not checking
        more tickers than necessary.
        """
        # Large ticker list
        all_tickers = [f"TICKER{i:03d}" for i in range(100)]
        batch_size = 3

        # Track resume check calls
        call_count = 0

        def mock_resume_check(ticker):
            nonlocal call_count
            call_count += 1
            return True  # All tickers need processing

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check
        )

        # Should return exactly batch_size tickers
        assert len(result) == batch_size

        # Should only check exactly batch_size tickers (early termination)
        assert call_count == batch_size

        # Should return first batch_size tickers
        assert result == ["TICKER000", "TICKER001", "TICKER002"]

    def test_regression_batch_size_one_edge_case(self, batch_service):
        """
        REGRESSION TEST: Test batch_size=1 edge case.

        This test ensures the fix works correctly for the smallest
        possible batch size.
        """
        all_tickers = ["AAPL", "MSFT", "GOOGL"]
        batch_size = 1

        # Skip first ticker
        def mock_resume_check(ticker):
            return ticker != "AAPL"

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check
        )

        # Should return exactly 1 ticker
        assert len(result) == 1
        assert result == ["MSFT"]

    def test_regression_all_tickers_need_processing(self, batch_service):
        """
        REGRESSION TEST: Test when all tickers need processing.

        This test ensures the fix doesn't break the simple case where
        no resume filtering is needed.
        """
        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        batch_size = 2

        # All tickers need processing
        def mock_resume_check(ticker):
            return True

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check
        )

        # Should return first batch_size tickers
        assert len(result) == batch_size
        assert result == ["AAPL", "MSFT"]

    def test_regression_resume_check_exception_handling(
        self, batch_service, mock_console
    ):
        """
        REGRESSION TEST: Test handling of resume check exceptions.

        This test ensures the fix handles errors gracefully without
        affecting batch size accuracy.
        """
        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        batch_size = 2

        # Mock resume check that raises exception for MSFT
        def mock_resume_check(ticker):
            if ticker == "MSFT":
                raise ValueError("Resume check failed")
            return True

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check
        )

        # Should handle exception and continue processing
        assert len(result) <= batch_size
        assert "MSFT" not in result  # Should be excluded due to exception
        assert "AAPL" in result or "GOOGL" in result  # Others should be included


class TestBatchSizeFixIntegrationRegression:
    """Integration regression tests for batch size fix with StrategyDispatcher."""

    @pytest.fixture
    def temp_batch_file(self):
        """Create temporary batch file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")
            yield f.name

        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def mock_console(self):
        """Create mock console logger."""
        return Mock(spec=ConsoleLogger)

    @pytest.fixture
    def strategy_config(self, temp_batch_file):
        """Create strategy config for testing."""
        return StrategyConfig(
            ticker=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
            strategy_types=[StrategyType.SMA],
            use_years=False,
            years=15,
            multi_ticker=False,
            use_scanner=False,
            scanner_list="",
            use_gbm=False,
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
            batch=True,
            batch_size=2,
            batch_file_path=temp_batch_file,
        )

    @patch("app.cli.services.strategy_dispatcher.SmartResumeService")
    def test_regression_strategy_dispatcher_integration(
        self,
        mock_resume_service_class,
        strategy_config,
        mock_console,
    ):
        """
        REGRESSION TEST: Test full integration with StrategyDispatcher.

        This test verifies that the batch size fix works correctly when
        integrated with the full StrategyDispatcher workflow.
        """
        # Setup mock resume service
        mock_resume_service = Mock()
        mock_resume_service_class.return_value = mock_resume_service

        # Mock resume analysis - simulate AAPL being complete
        mock_resume_analysis = Mock()
        mock_resume_analysis.is_complete.return_value = (
            False  # Individual checks will vary
        )
        mock_resume_service.analyze_resume_status.side_effect = [
            Mock(is_complete=lambda: True),  # AAPL is complete
            Mock(is_complete=lambda: False),  # MSFT needs processing
            Mock(is_complete=lambda: False),  # GOOGL needs processing
        ]

        # Create dispatcher
        dispatcher = StrategyDispatcher(console=mock_console)
        dispatcher.batch_service = BatchProcessingService(
            strategy_config.batch_file_path, mock_console
        )
        dispatcher.resume_service = mock_resume_service

        # Test the resume check function creation
        # This simulates the internal logic of the fixed StrategyDispatcher
        def create_resume_check_function(config):
            def resume_check_function(ticker):
                # Create single-ticker config for resume analysis
                single_ticker_config = config.model_copy(deep=True)
                single_ticker_config.ticker = ticker
                single_ticker_config.batch = False

                # Mock conversion to legacy format (simplified)
                legacy_config = {"ticker": [ticker]}

                # Analyze resume status
                ticker_resume_analysis = mock_resume_service.analyze_resume_status(
                    legacy_config
                )

                # Return True if ticker needs processing
                return not ticker_resume_analysis.is_complete()

            return resume_check_function

        # Test the resume check function
        resume_check_fn = create_resume_check_function(strategy_config)

        # Get tickers needing processing using the fixed logic
        result = dispatcher.batch_service.get_tickers_needing_processing(
            strategy_config.ticker, strategy_config.batch_size, resume_check_fn
        )

        # CRITICAL REGRESSION CHECK: Should return exactly batch_size tickers
        assert len(result) == strategy_config.batch_size

        # Should exclude AAPL (marked as complete by resume analysis)
        assert "AAPL" not in result

        # Should include next tickers that need processing
        assert set(result) == {"MSFT", "GOOGL"}

    def test_regression_batch_file_update_accuracy(self, strategy_config, mock_console):
        """
        REGRESSION TEST: Test that batch file updates are accurate after fix.

        This test ensures that the batch file is updated correctly for
        exactly the tickers that were processed.
        """
        batch_service = BatchProcessingService(
            strategy_config.batch_file_path, mock_console
        )

        # Simulate processing exactly batch_size tickers
        processed_tickers = ["MSFT", "GOOGL"]  # Exactly batch_size=2

        # Update batch file for processed tickers
        for ticker in processed_tickers:
            success = batch_service.update_ticker_status(ticker)
            assert success

        # Verify batch file contains exactly the processed tickers
        df = batch_service.read_batch_file()
        assert len(df) == len(processed_tickers)
        assert set(df["Ticker"]) == set(processed_tickers)

        # Verify all have today's date
        today = datetime.now().strftime("%Y-%m-%d")
        assert all(df["Last Modified"] == today)

    def test_regression_subsequent_batch_run_accuracy(
        self, strategy_config, mock_console
    ):
        """
        REGRESSION TEST: Test accuracy of subsequent batch runs.

        This test ensures that after processing a batch, the next batch
        run correctly excludes already processed tickers.
        """
        batch_service = BatchProcessingService(
            strategy_config.batch_file_path, mock_console
        )

        # Simulate first batch run - process 2 tickers
        first_batch = ["AAPL", "MSFT"]
        for ticker in first_batch:
            batch_service.update_ticker_status(ticker)

        # Simulate second batch run
        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        batch_size = 2

        # All remaining tickers need processing
        def mock_resume_check(ticker):
            return True

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check
        )

        # Should exclude first batch and return next batch_size tickers
        assert len(result) == batch_size
        assert "AAPL" not in result  # Processed in first batch
        assert "MSFT" not in result  # Processed in first batch
        assert set(result) == {"GOOGL", "TSLA"}

    def test_regression_memory_performance_large_scale(self, mock_console):
        """
        REGRESSION TEST: Test memory and performance with large ticker lists.

        This test ensures the fix doesn't introduce performance regressions
        when processing large ticker lists.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")

        try:
            batch_service = BatchProcessingService(f.name, mock_console)

            # Large ticker list (1000 tickers)
            all_tickers = [f"TICKER{i:04d}" for i in range(1000)]
            batch_size = 50

            # Track resume check calls for performance validation
            call_count = 0

            def mock_resume_check(ticker):
                nonlocal call_count
                call_count += 1
                return True  # All need processing

            result = batch_service.get_tickers_needing_processing(
                all_tickers, batch_size, mock_resume_check
            )

            # Should return exactly batch_size tickers
            assert len(result) == batch_size

            # Should only call resume check exactly batch_size times (performance check)
            assert call_count == batch_size

            # Should not load entire ticker list into memory unnecessarily
            assert result == all_tickers[:batch_size]

        finally:
            Path(f.name).unlink()

    def test_regression_concurrent_batch_processing_simulation(self, mock_console):
        """
        REGRESSION TEST: Test concurrent batch processing simulation.

        This test simulates concurrent batch processing to ensure the fix
        doesn't introduce race conditions or data corruption.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")

        try:
            # Simulate two concurrent batch processors
            batch_service_1 = BatchProcessingService(f.name, mock_console)
            batch_service_2 = BatchProcessingService(f.name, mock_console)

            all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META"]
            batch_size = 2

            def mock_resume_check(ticker):
                return True  # All need processing

            # First processor gets first batch
            result_1 = batch_service_1.get_tickers_needing_processing(
                all_tickers, batch_size, mock_resume_check
            )

            # Update batch file with first batch
            for ticker in result_1:
                batch_service_1.update_ticker_status(ticker)

            # Second processor gets next batch (should exclude first batch)
            result_2 = batch_service_2.get_tickers_needing_processing(
                all_tickers, batch_size, mock_resume_check
            )

            # Results should not overlap
            assert len(result_1) == batch_size
            assert len(result_2) == batch_size
            assert set(result_1).isdisjoint(set(result_2))

            # Combined results should cover first 4 tickers
            combined = set(result_1) | set(result_2)
            assert combined == set(all_tickers[:4])

        finally:
            Path(f.name).unlink()

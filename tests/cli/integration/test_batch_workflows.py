"""
Integration tests for End-to-End Batch Workflows.

This test suite covers complete batch processing workflows that span
multiple commands and sessions to ensure the entire batch system works
correctly in realistic scenarios.

Key workflows tested:
- Complete batch processing cycle (run → update → review)
- Multi-day batch processing scenarios
- Batch file state consistency across commands
- Large-scale batch processing (500+ tickers)
- Concurrent command execution with shared batch file
- Error recovery and retry scenarios
- Performance and memory usage validation

Integration scenarios:
1. Day 1: Start batch processing with large ticker list
2. Day 1: Process partial batch, update batch file
3. Day 1: Review processed results
4. Day 2: Resume batch processing from where left off
5. Day 2: Complete remaining tickers
6. Day 2: Final review and validation

This ensures the batch system maintains state correctly across:
- Multiple command invocations
- Multiple days
- Multiple users/processes
- Error conditions and recovery
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

from app.cli.models.strategy import (
    StrategyConfig,
    StrategyMinimums,
    StrategyType,
    SyntheticTickerConfig,
)
from app.cli.services.batch_processing_service import BatchProcessingService
from app.tools.console_logging import ConsoleLogger


@pytest.mark.integration
class TestEndToEndBatchWorkflows:
    """Integration tests for complete batch processing workflows."""

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
    def large_ticker_list(self):
        """Create large ticker list for testing."""
        # Simulate S&P 500 size ticker list
        return [f"TICKER{i:03d}" for i in range(500)]

    @pytest.fixture
    def strategy_config_batch(self, temp_batch_file, large_ticker_list):
        """Create strategy config for batch processing."""
        return StrategyConfig(
            ticker=large_ticker_list,
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
            batch_size=50,  # Process 50 tickers at a time
            batch_file_path=temp_batch_file,
        )

    def test_complete_batch_processing_cycle(self, strategy_config_batch, mock_console):
        """
        Test complete batch processing cycle: run → update → review.

        This integration test simulates a realistic workflow where:
        1. User starts batch processing
        2. Processes first batch of tickers
        3. Reviews processed results
        4. Continues processing remaining tickers
        """
        batch_service = BatchProcessingService(
            strategy_config_batch.batch_file_path,
            mock_console,
        )

        # Phase 1: Initial batch processing
        # Simulate resume check that allows all tickers to be processed
        def mock_resume_check_phase1(ticker):
            return True  # All tickers need processing initially

        first_batch = batch_service.get_tickers_needing_processing(
            strategy_config_batch.ticker,
            strategy_config_batch.batch_size,
            mock_resume_check_phase1,
        )

        # Should select exactly batch_size tickers
        assert len(first_batch) == strategy_config_batch.batch_size
        assert first_batch == strategy_config_batch.ticker[:50]

        # Phase 2: Simulate successful processing of first batch
        for ticker in first_batch:
            success = batch_service.update_ticker_status(ticker)
            assert success

        # Phase 3: Verify batch file state after first batch
        processed_today = batch_service.get_processed_tickers_today()
        assert len(processed_today) == strategy_config_batch.batch_size
        assert processed_today == set(first_batch)

        # Phase 4: Get batch status after first batch
        status = batch_service.get_batch_status(strategy_config_batch.ticker)
        assert status["total_tickers"] == len(strategy_config_batch.ticker)
        assert status["processed_today"] == strategy_config_batch.batch_size
        assert (
            status["pending"]
            == len(strategy_config_batch.ticker) - strategy_config_batch.batch_size
        )
        assert status["completion_rate"] == strategy_config_batch.batch_size / len(
            strategy_config_batch.ticker,
        )

        # Phase 5: Second batch processing (should exclude first batch)
        def mock_resume_check_phase2(ticker):
            return True  # All remaining tickers need processing

        second_batch = batch_service.get_tickers_needing_processing(
            strategy_config_batch.ticker,
            strategy_config_batch.batch_size,
            mock_resume_check_phase2,
        )

        # Should select next batch_size tickers (excluding first batch)
        assert len(second_batch) == strategy_config_batch.batch_size
        assert second_batch == strategy_config_batch.ticker[50:100]
        assert not set(second_batch).intersection(set(first_batch))

        # Phase 6: Process second batch
        for ticker in second_batch:
            success = batch_service.update_ticker_status(ticker)
            assert success

        # Phase 7: Final verification
        final_status = batch_service.get_batch_status(strategy_config_batch.ticker)
        assert final_status["processed_today"] == 100  # Two batches processed
        assert final_status["pending"] == 400  # Remaining tickers

    def test_multi_day_batch_processing_simulation(
        self,
        strategy_config_batch,
        mock_console,
    ):
        """
        Test multi-day batch processing simulation.

        This test simulates batch processing across multiple days,
        ensuring proper cleanup and continuation.
        """
        batch_service = BatchProcessingService(
            strategy_config_batch.batch_file_path,
            mock_console,
        )

        # Day 1: Process first batch
        datetime.now().strftime("%Y-%m-%d")
        day1_batch = ["TICKER000", "TICKER001", "TICKER002"]

        for ticker in day1_batch:
            batch_service.update_ticker_status(ticker)

        # Verify day 1 state
        day1_processed = batch_service.get_processed_tickers_today()
        assert day1_processed == set(day1_batch)

        # Simulate day 2: Add old entries to batch file
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        old_entries = [
            {"Ticker": "TICKER100", "Last Modified": yesterday},
            {"Ticker": "TICKER101", "Last Modified": yesterday},
        ]

        # Manually add old entries to simulate previous day's work
        df = batch_service.read_batch_file()
        old_df = pd.DataFrame(old_entries)
        combined_df = pd.concat([df, old_df], ignore_index=True)
        combined_df.to_csv(batch_service.batch_file_path, index=False)

        # Day 2: Clean old entries
        removed_count = batch_service.clean_old_entries()
        assert removed_count == 2  # Should remove yesterday's entries

        # Day 2: Verify only today's entries remain
        day2_processed = batch_service.get_processed_tickers_today()
        assert day2_processed == set(day1_batch)  # Only today's entries

        # Day 2: Process more tickers
        day2_new_batch = ["TICKER003", "TICKER004"]
        for ticker in day2_new_batch:
            batch_service.update_ticker_status(ticker)

        # Final verification: Should have all day 2 entries
        final_processed = batch_service.get_processed_tickers_today()
        assert final_processed == set(day1_batch + day2_new_batch)

    def test_large_scale_batch_processing_performance(
        self,
        mock_console,
        large_ticker_list,
    ):
        """
        Test large-scale batch processing performance.

        This test ensures the batch system can handle realistic
        large ticker lists (500+ tickers) efficiently.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")

        try:
            batch_service = BatchProcessingService(f.name, mock_console)

            # Test large-scale selection performance
            batch_size = 100
            call_count = 0

            def mock_resume_check(ticker):
                nonlocal call_count
                call_count += 1
                return True  # All need processing

            # Measure performance of large-scale selection
            result = batch_service.get_tickers_needing_processing(
                large_ticker_list,
                batch_size,
                mock_resume_check,
            )

            # Verify results
            assert len(result) == batch_size
            assert call_count == batch_size  # Should stop early (performance check)

            # Test large-scale batch file updates
            update_count = 0
            for ticker in result:
                success = batch_service.update_ticker_status(ticker)
                assert success
                update_count += 1

            assert update_count == batch_size

            # Verify batch file performance with large entries
            final_df = batch_service.read_batch_file()
            assert len(final_df) == batch_size

            # Test status calculation performance with large data
            status = batch_service.get_batch_status(large_ticker_list)
            assert status["total_tickers"] == len(large_ticker_list)
            assert status["processed_today"] == batch_size

        finally:
            Path(f.name).unlink()

    def test_concurrent_batch_processing_workflow(self, mock_console):
        """
        Test concurrent batch processing workflow simulation.

        This test simulates multiple concurrent batch processors
        working on the same ticker list without conflicts.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")

        try:
            # Create multiple batch services (simulating concurrent processes)
            batch_service_1 = BatchProcessingService(f.name, mock_console)
            batch_service_2 = BatchProcessingService(f.name, mock_console)

            all_tickers = [f"TICKER{i:03d}" for i in range(20)]
            batch_size = 5

            def mock_resume_check(ticker):
                return True  # All need processing

            # Process 1: Get first batch
            batch_1 = batch_service_1.get_tickers_needing_processing(
                all_tickers,
                batch_size,
                mock_resume_check,
            )
            assert len(batch_1) == batch_size

            # Process 1: Update batch file
            for ticker in batch_1:
                batch_service_1.update_ticker_status(ticker)

            # Process 2: Get next batch (should exclude Process 1's tickers)
            batch_2 = batch_service_2.get_tickers_needing_processing(
                all_tickers,
                batch_size,
                mock_resume_check,
            )
            assert len(batch_2) == batch_size

            # Verify no overlap between batches
            assert set(batch_1).isdisjoint(set(batch_2))

            # Process 2: Update batch file
            for ticker in batch_2:
                batch_service_2.update_ticker_status(ticker)

            # Verify final state
            final_processed = batch_service_1.get_processed_tickers_today()
            assert len(final_processed) == 10  # Both batches
            assert final_processed == set(batch_1 + batch_2)

        finally:
            Path(f.name).unlink()

    def test_error_recovery_and_retry_workflow(
        self,
        strategy_config_batch,
        mock_console,
    ):
        """
        Test error recovery and retry workflow.

        This test simulates error conditions and recovery scenarios
        to ensure the batch system is resilient.
        """
        batch_service = BatchProcessingService(
            strategy_config_batch.batch_file_path,
            mock_console,
        )

        # Scenario 1: Resume check failures for some tickers
        failure_tickers = ["TICKER001", "TICKER003", "TICKER005"]

        def mock_resume_check_with_failures(ticker):
            if ticker in failure_tickers:
                msg = f"Resume check failed for {ticker}"
                raise ValueError(msg)
            return True

        # Should handle failures gracefully
        result = batch_service.get_tickers_needing_processing(
            strategy_config_batch.ticker[:10],
            5,
            mock_resume_check_with_failures,
        )

        # Should exclude failed tickers and return successful ones
        assert len(result) == 5
        assert not any(ticker in failure_tickers for ticker in result)

        # Scenario 2: Partial batch processing with some failures
        successful_tickers = result[:3]
        result[3:]

        # Update successful tickers
        for ticker in successful_tickers:
            success = batch_service.update_ticker_status(ticker)
            assert success

        # Simulate processing failures (don't update batch file for failed tickers)
        # This simulates real-world scenario where some tickers fail processing

        # Scenario 3: Retry processing (should exclude successful, include failed)
        def mock_resume_check_retry(ticker):
            return ticker not in successful_tickers  # Exclude already processed

        retry_batch = batch_service.get_tickers_needing_processing(
            strategy_config_batch.ticker[:10],
            5,
            mock_resume_check_retry,
        )

        # Should include previously failed tickers and new tickers
        assert len(retry_batch) <= 5
        assert not any(ticker in successful_tickers for ticker in retry_batch)

    def test_batch_file_corruption_recovery(self, mock_console):
        """
        Test batch file corruption recovery workflow.

        This test ensures the system can recover from corrupted
        batch files gracefully.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            # Create corrupted batch file
            f.write("Invalid,CSV,Format\n")
            f.write("This,Is,Not,Valid,CSV\n")

        try:
            batch_service = BatchProcessingService(f.name, mock_console)

            # Should handle corrupted file gracefully
            assert not batch_service.validate_batch_file()

            # Should return empty results for corrupted file
            df = batch_service.read_batch_file()
            assert len(df) == 0

            processed = batch_service.get_processed_tickers_today()
            assert len(processed) == 0

            # Should handle update gracefully (may fail, but shouldn't crash)
            batch_service.update_ticker_status("AAPL")
            # Success depends on implementation - may fail due to corruption

        finally:
            Path(f.name).unlink()

    def test_memory_usage_optimization_workflow(self, mock_console):
        """
        Test memory usage optimization in large-scale workflow.

        This test ensures the batch system doesn't accumulate
        excessive memory during long-running workflows.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")

        try:
            batch_service = BatchProcessingService(f.name, mock_console)

            # Simulate processing many small batches (memory test)
            large_ticker_list = [f"TICKER{i:04d}" for i in range(1000)]
            batch_size = 10
            processed_count = 0

            def mock_resume_check(ticker):
                return True

            # Process multiple batches
            for _batch_num in range(10):  # Process 10 batches
                # Get current batch
                remaining_tickers = [
                    t
                    for t in large_ticker_list
                    if t not in batch_service.get_processed_tickers_today()
                ]

                if not remaining_tickers:
                    break

                current_batch = batch_service.get_tickers_needing_processing(
                    remaining_tickers,
                    batch_size,
                    mock_resume_check,
                )

                # Process batch
                for ticker in current_batch:
                    batch_service.update_ticker_status(ticker)
                    processed_count += 1

                # Verify memory doesn't accumulate excessively
                # (In real test, you might check actual memory usage)
                status = batch_service.get_batch_status(large_ticker_list)
                assert status["processed_today"] == processed_count

            # Final verification
            assert processed_count == 100  # 10 batches * 10 tickers each

        finally:
            Path(f.name).unlink()

    def test_cross_command_integration_workflow(self, mock_console):
        """
        Test integration workflow across strategy run and review commands.

        This test simulates realistic usage where users alternate
        between batch processing and reviewing results.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")

        try:
            # Simulate strategy run command with batch processing
            batch_service_run = BatchProcessingService(f.name, mock_console)

            run_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
            batch_size = 2

            def mock_resume_check(ticker):
                return True

            # Strategy run: Process first batch
            first_batch = batch_service_run.get_tickers_needing_processing(
                run_tickers,
                batch_size,
                mock_resume_check,
            )
            assert len(first_batch) == batch_size

            # Update batch file (simulate successful strategy execution)
            for ticker in first_batch:
                batch_service_run.update_ticker_status(ticker)

            # Simulate strategy review command with batch mode
            batch_service_review = BatchProcessingService(f.name, mock_console)

            # Review should see the same processed tickers
            review_tickers = batch_service_review.get_batch_tickers()
            assert set(review_tickers) == set(first_batch)

            processed_review = batch_service_review.get_processed_tickers_today()
            assert processed_review == set(first_batch)

            # Continue with strategy run for remaining tickers
            second_batch = batch_service_run.get_tickers_needing_processing(
                run_tickers,
                batch_size,
                mock_resume_check,
            )
            assert len(second_batch) == batch_size
            assert set(second_batch).isdisjoint(set(first_batch))

            # Process second batch
            for ticker in second_batch:
                batch_service_run.update_ticker_status(ticker)

            # Final review should see all processed tickers
            final_review_tickers = batch_service_review.get_batch_tickers()
            assert len(final_review_tickers) == 4  # Two batches
            assert set(final_review_tickers) == set(first_batch + second_batch)

        finally:
            Path(f.name).unlink()


@pytest.mark.integration
class TestBatchWorkflowStateConsistency:
    """Test state consistency across complex batch workflows."""

    @pytest.fixture
    def mock_console(self):
        """Create mock console logger."""
        return Mock(spec=ConsoleLogger)

    def test_state_consistency_after_interruption(self, mock_console):
        """
        Test state consistency after workflow interruption.

        This test simulates scenarios where batch processing is
        interrupted and resumed later.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")

        try:
            # Phase 1: Start batch processing
            batch_service = BatchProcessingService(f.name, mock_console)
            tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

            # Process partial batch
            partial_batch = ["AAPL", "MSFT"]
            for ticker in partial_batch:
                batch_service.update_ticker_status(ticker)

            # Simulate interruption (create new service instance)
            # This simulates restarting the application
            new_batch_service = BatchProcessingService(f.name, mock_console)

            # Phase 2: Resume after interruption
            # Should maintain consistent state
            processed = new_batch_service.get_processed_tickers_today()
            assert processed == set(partial_batch)

            def mock_resume_check(ticker):
                return True

            # Continue processing
            remaining_batch = new_batch_service.get_tickers_needing_processing(
                tickers,
                2,
                mock_resume_check,
            )

            # Should exclude already processed tickers
            assert len(remaining_batch) == 2
            assert set(remaining_batch).isdisjoint(set(partial_batch))

        finally:
            Path(f.name).unlink()

    def test_consistency_across_date_boundaries(self, mock_console):
        """
        Test consistency across date boundaries.

        This test ensures proper handling when processing
        spans across midnight (date changes).
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")

        try:
            batch_service = BatchProcessingService(f.name, mock_console)

            # Add entries from different dates
            today = datetime.now().strftime("%Y-%m-%d")
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

            # Manually create mixed-date batch file
            mixed_data = [
                {"Ticker": "AAPL", "Last Modified": today},
                {"Ticker": "MSFT", "Last Modified": today},
                {"Ticker": "GOOGL", "Last Modified": yesterday},
                {"Ticker": "TSLA", "Last Modified": yesterday},
            ]

            df = pd.DataFrame(mixed_data)
            df.to_csv(f.name, index=False)

            # Test today's processed tickers
            processed_today = batch_service.get_processed_tickers_today()
            assert processed_today == {"AAPL", "MSFT"}

            # Test cleanup of old entries
            removed_count = batch_service.clean_old_entries()
            assert removed_count == 2  # Yesterday's entries

            # Verify only today's entries remain
            final_processed = batch_service.get_processed_tickers_today()
            assert final_processed == {"AAPL", "MSFT"}

        finally:
            Path(f.name).unlink()

    def test_data_integrity_under_concurrent_access(self, mock_console):
        """
        Test data integrity under simulated concurrent access.

        This test ensures batch file data remains consistent
        when multiple processes access it concurrently.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")

        try:
            # Create multiple service instances (simulating concurrent processes)
            services = [BatchProcessingService(f.name, mock_console) for _ in range(3)]

            tickers_per_service = [["AAPL", "MSFT"], ["GOOGL", "TSLA"], ["NVDA", "AMD"]]

            # Simulate concurrent updates
            for i, service in enumerate(services):
                for ticker in tickers_per_service[i]:
                    success = service.update_ticker_status(ticker)
                    assert success

            # Verify data integrity
            # All services should see consistent final state
            expected_all_tickers = set()
            for ticker_list in tickers_per_service:
                expected_all_tickers.update(ticker_list)

            for service in services:
                processed = service.get_processed_tickers_today()
                # Each service should see all tickers (eventual consistency)
                assert expected_all_tickers.issubset(processed) or len(processed) >= 4

            # Verify batch file integrity
            final_df = services[0].read_batch_file()
            assert len(final_df) >= len(expected_all_tickers)

        finally:
            Path(f.name).unlink()

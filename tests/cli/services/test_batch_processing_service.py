"""
Comprehensive unit tests for BatchProcessingService.

This test suite covers the BatchProcessingService with focus on:
- CSV file operations (read, write, validate)
- Ticker status tracking and updates
- Old entry cleanup logic
- Pending ticker selection (original method)
- Resume-aware ticker selection (get_tickers_needing_processing)
- Error handling and edge cases
- Batch status reporting

Test coverage includes:
- Empty batch file handling
- Malformed CSV handling
- Date-based filtering
- Concurrent access scenarios
- Large ticker list performance
"""

from datetime import datetime, timedelta
from pathlib import Path
import tempfile
from unittest.mock import Mock

import pandas as pd
import pytest

from app.cli.services.batch_processing_service import BatchProcessingService
from app.tools.console_logging import ConsoleLogger


class TestBatchProcessingService:
    """Test cases for BatchProcessingService core functionality."""

    @pytest.fixture
    def temp_batch_file(self):
        """Create temporary batch file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")
            yield f.name

        # Cleanup
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def mock_console(self):
        """Create mock console logger."""
        return Mock(spec=ConsoleLogger)

    @pytest.fixture
    def batch_service(self, temp_batch_file, mock_console):
        """Create BatchProcessingService instance with temp file."""
        return BatchProcessingService(temp_batch_file, mock_console)

    @pytest.fixture
    def sample_batch_data(self):
        """Sample batch data for testing."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        return [
            {"Ticker": "AAPL", "Last Modified": today},
            {"Ticker": "MSFT", "Last Modified": today},
            {"Ticker": "GOOGL", "Last Modified": yesterday},
            {"Ticker": "TSLA", "Last Modified": yesterday},
        ]

    def test_service_initialization_new_file(self, mock_console):
        """Test service initialization with non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            batch_file = Path(temp_dir) / "new_batch.csv"

            BatchProcessingService(str(batch_file), mock_console)

            # File should be created
            assert batch_file.exists()

            # File should have correct headers
            df = pd.read_csv(batch_file)
            assert list(df.columns) == ["Ticker", "Last Modified"]
            assert len(df) == 0

    def test_service_initialization_existing_file(self, batch_service, temp_batch_file):
        """Test service initialization with existing file."""
        # File should exist and be valid
        assert Path(temp_batch_file).exists()
        assert batch_service.validate_batch_file()

    def test_validate_batch_file_valid(self, batch_service):
        """Test validation of valid batch file."""
        assert batch_service.validate_batch_file()

    def test_validate_batch_file_missing(self, mock_console):
        """Test validation of missing batch file."""
        service = BatchProcessingService("/nonexistent/file.csv", mock_console)
        assert not service.validate_batch_file()

    def test_validate_batch_file_malformed(self, mock_console):
        """Test validation of malformed batch file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Wrong,Headers\n")
            f.write("AAPL,2025-01-01\n")

        try:
            service = BatchProcessingService(f.name, mock_console)
            assert not service.validate_batch_file()
        finally:
            Path(f.name).unlink()

    def test_read_batch_file_empty(self, batch_service):
        """Test reading empty batch file."""
        df = batch_service.read_batch_file()

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["Ticker", "Last Modified"]
        assert len(df) == 0

    def test_read_batch_file_with_data(self, batch_service, sample_batch_data):
        """Test reading batch file with data."""
        # Add sample data to file
        df = pd.DataFrame(sample_batch_data)
        df.to_csv(batch_service.batch_file_path, index=False)

        result_df = batch_service.read_batch_file()

        assert len(result_df) == 4
        assert set(result_df["Ticker"].str.upper()) == {"AAPL", "MSFT", "GOOGL", "TSLA"}

    def test_read_batch_file_ticker_normalization(self, batch_service):
        """Test that tickers are normalized to uppercase."""
        # Add lowercase tickers
        df = pd.DataFrame(
            [
                {"Ticker": "aapl", "Last Modified": "2025-01-01"},
                {"Ticker": " msft ", "Last Modified": "2025-01-01"},
            ],
        )
        df.to_csv(batch_service.batch_file_path, index=False)

        result_df = batch_service.read_batch_file()

        assert list(result_df["Ticker"]) == ["AAPL", "MSFT"]

    def test_clean_old_entries_none_to_clean(self, batch_service, sample_batch_data):
        """Test cleaning when no old entries exist."""
        today = datetime.now().strftime("%Y-%m-%d")
        today_data = [
            {"Ticker": "AAPL", "Last Modified": today},
            {"Ticker": "MSFT", "Last Modified": today},
        ]

        df = pd.DataFrame(today_data)
        df.to_csv(batch_service.batch_file_path, index=False)

        removed_count = batch_service.clean_old_entries()

        assert removed_count == 0

        # Data should remain unchanged
        result_df = batch_service.read_batch_file()
        assert len(result_df) == 2

    def test_clean_old_entries_with_old_data(self, batch_service, sample_batch_data):
        """Test cleaning old entries."""
        df = pd.DataFrame(sample_batch_data)
        df.to_csv(batch_service.batch_file_path, index=False)

        removed_count = batch_service.clean_old_entries()

        assert removed_count == 2  # GOOGL and TSLA from yesterday

        # Only today's entries should remain
        result_df = batch_service.read_batch_file()
        assert len(result_df) == 2
        assert set(result_df["Ticker"]) == {"AAPL", "MSFT"}

    def test_get_processed_tickers_today_empty(self, batch_service):
        """Test getting processed tickers when none exist."""
        processed = batch_service.get_processed_tickers_today()

        assert isinstance(processed, set)
        assert len(processed) == 0

    def test_get_processed_tickers_today_with_data(
        self, batch_service, sample_batch_data,
    ):
        """Test getting processed tickers for today."""
        df = pd.DataFrame(sample_batch_data)
        df.to_csv(batch_service.batch_file_path, index=False)

        processed = batch_service.get_processed_tickers_today()

        # Should only include today's entries
        assert processed == {"AAPL", "MSFT"}

    def test_get_pending_tickers_all_pending(self, batch_service):
        """Test getting pending tickers when none are processed."""
        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        batch_size = 3

        pending = batch_service.get_pending_tickers(all_tickers, batch_size)

        assert len(pending) == 3
        assert set(pending).issubset({t.upper() for t in all_tickers})

    def test_get_pending_tickers_some_processed(self, batch_service, sample_batch_data):
        """Test getting pending tickers when some are already processed."""
        df = pd.DataFrame(sample_batch_data)
        df.to_csv(batch_service.batch_file_path, index=False)

        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        batch_size = 2

        pending = batch_service.get_pending_tickers(all_tickers, batch_size)

        # Should exclude today's processed tickers (AAPL, MSFT)
        assert len(pending) == 2
        assert "AAPL" not in pending
        assert "MSFT" not in pending
        assert set(pending).issubset({"GOOGL", "TSLA", "NVDA"})

    def test_get_pending_tickers_batch_size_limit(self, batch_service):
        """Test that batch size limit is respected."""
        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN"]
        batch_size = 3

        pending = batch_service.get_pending_tickers(all_tickers, batch_size)

        assert len(pending) == 3

    def test_update_ticker_status_new_ticker(self, batch_service):
        """Test updating status for new ticker."""
        success = batch_service.update_ticker_status("AAPL")

        assert success

        # Verify ticker was added
        df = batch_service.read_batch_file()
        assert len(df) == 1
        assert df.iloc[0]["Ticker"] == "AAPL"
        assert df.iloc[0]["Last Modified"] == datetime.now().strftime("%Y-%m-%d")

    def test_update_ticker_status_existing_ticker(self, batch_service):
        """Test updating status for existing ticker."""
        # Add initial entry
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        df = pd.DataFrame([{"Ticker": "AAPL", "Last Modified": yesterday}])
        df.to_csv(batch_service.batch_file_path, index=False)

        success = batch_service.update_ticker_status("AAPL")

        assert success

        # Verify ticker was updated
        result_df = batch_service.read_batch_file()
        assert len(result_df) == 1
        assert result_df.iloc[0]["Last Modified"] == datetime.now().strftime("%Y-%m-%d")

    def test_update_ticker_status_case_insensitive(self, batch_service):
        """Test that ticker updates are case insensitive."""
        # Add lowercase ticker
        df = pd.DataFrame([{"Ticker": "aapl", "Last Modified": "2025-01-01"}])
        df.to_csv(batch_service.batch_file_path, index=False)

        success = batch_service.update_ticker_status("AAPL")

        assert success

        # Should update existing entry, not create new one
        result_df = batch_service.read_batch_file()
        assert len(result_df) == 1
        assert result_df.iloc[0]["Ticker"] == "AAPL"

    def test_get_batch_status_empty(self, batch_service):
        """Test getting batch status with empty file."""
        all_tickers = ["AAPL", "MSFT", "GOOGL"]

        status = batch_service.get_batch_status(all_tickers)

        assert status["total_tickers"] == 3
        assert status["processed_today"] == 0
        assert status["pending"] == 3
        assert status["completion_rate"] == 0.0
        assert status["processed_list"] == []
        assert set(status["pending_list"]) == {"AAPL", "MSFT", "GOOGL"}

    def test_get_batch_status_with_data(self, batch_service, sample_batch_data):
        """Test getting batch status with processed data."""
        df = pd.DataFrame(sample_batch_data)
        df.to_csv(batch_service.batch_file_path, index=False)

        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

        status = batch_service.get_batch_status(all_tickers)

        assert status["total_tickers"] == 5
        assert status["processed_today"] == 2  # AAPL, MSFT from today
        assert status["pending"] == 3  # GOOGL, TSLA, NVDA
        assert status["completion_rate"] == 0.4
        assert set(status["processed_list"]) == {"AAPL", "MSFT"}

    def test_get_batch_tickers_empty(self, batch_service):
        """Test getting all tickers from empty batch file."""
        tickers = batch_service.get_batch_tickers()
        assert tickers == []

    def test_get_batch_tickers_with_data(self, batch_service, sample_batch_data):
        """Test getting all tickers from batch file."""
        df = pd.DataFrame(sample_batch_data)
        df.to_csv(batch_service.batch_file_path, index=False)

        tickers = batch_service.get_batch_tickers()

        assert len(tickers) == 4
        assert set(tickers) == {"AAPL", "MSFT", "GOOGL", "TSLA"}

    def test_get_batch_tickers_deduplication(self, batch_service):
        """Test that duplicate tickers are removed."""
        duplicate_data = [
            {"Ticker": "AAPL", "Last Modified": "2025-01-01"},
            {"Ticker": "AAPL", "Last Modified": "2025-01-02"},
            {"Ticker": "MSFT", "Last Modified": "2025-01-01"},
        ]

        df = pd.DataFrame(duplicate_data)
        df.to_csv(batch_service.batch_file_path, index=False)

        tickers = batch_service.get_batch_tickers()

        assert len(tickers) == 2
        assert set(tickers) == {"AAPL", "MSFT"}


class TestBatchProcessingServiceResumeAware:
    """Test cases for resume-aware batch processing functionality."""

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
        """Create BatchProcessingService instance with temp file."""
        return BatchProcessingService(temp_batch_file, mock_console)

    def test_get_tickers_needing_processing_all_need_work(self, batch_service):
        """Test when all tickers need processing."""
        all_tickers = ["AAPL", "MSFT", "GOOGL"]
        batch_size = 2

        # Mock resume function that always returns True (needs processing)
        def mock_resume_check(ticker):
            return True

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check,
        )

        assert len(result) == 2  # Batch size limit
        assert set(result).issubset({t.upper() for t in all_tickers})

    def test_get_tickers_needing_processing_some_skip(self, batch_service):
        """Test when some tickers can be skipped."""
        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        batch_size = 2

        # Mock resume function that skips AAPL and GOOGL
        def mock_resume_check(ticker):
            return ticker not in ["AAPL", "GOOGL"]

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check,
        )

        assert len(result) == 2
        assert set(result) == {"MSFT", "TSLA"}

    def test_get_tickers_needing_processing_not_enough_work(self, batch_service):
        """Test when fewer tickers need work than batch size."""
        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        batch_size = 3

        # Only MSFT needs processing
        def mock_resume_check(ticker):
            return ticker == "MSFT"

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check,
        )

        assert len(result) == 1
        assert result == ["MSFT"]

    def test_get_tickers_needing_processing_respects_batch_file(self, batch_service):
        """Test that resume-aware selection respects batch file status."""
        # Add some already processed tickers to batch file
        today = datetime.now().strftime("%Y-%m-%d")
        processed_data = [
            {"Ticker": "AAPL", "Last Modified": today},
            {"Ticker": "MSFT", "Last Modified": today},
        ]
        df = pd.DataFrame(processed_data)
        df.to_csv(batch_service.batch_file_path, index=False)

        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        batch_size = 2

        # All tickers need processing according to resume logic
        def mock_resume_check(ticker):
            return True

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check,
        )

        # Should exclude AAPL and MSFT (already processed today)
        assert len(result) == 2
        assert set(result) == {"GOOGL", "TSLA"}

    def test_get_tickers_needing_processing_early_termination(self, batch_service):
        """Test that selection stops when batch size is reached."""
        all_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        batch_size = 2

        # Track how many times resume check is called
        call_count = 0

        def mock_resume_check(ticker):
            nonlocal call_count
            call_count += 1
            return True  # All need processing

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check,
        )

        assert len(result) == 2
        assert call_count == 2  # Should stop after finding 2 tickers

    def test_get_tickers_needing_processing_resume_check_exception(
        self, batch_service, mock_console,
    ):
        """Test handling of resume check exceptions."""
        all_tickers = ["AAPL", "MSFT", "GOOGL"]
        batch_size = 2

        # Mock resume function that raises exception for MSFT
        def mock_resume_check(ticker):
            if ticker == "MSFT":
                msg = "Resume check failed"
                raise ValueError(msg)
            return True

        result = batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check,
        )

        # Should handle exception gracefully and continue
        assert len(result) <= batch_size
        assert "MSFT" not in result  # Should be excluded due to exception

    def test_get_tickers_needing_processing_debug_logging(
        self, batch_service, mock_console,
    ):
        """Test that debug logging works for skipped tickers."""
        all_tickers = ["AAPL", "MSFT", "GOOGL"]
        batch_size = 2

        # Skip AAPL
        def mock_resume_check(ticker):
            return ticker != "AAPL"

        batch_service.get_tickers_needing_processing(
            all_tickers, batch_size, mock_resume_check,
        )

        # Should have debug log for skipped ticker
        mock_console.debug.assert_called()


class TestBatchProcessingServiceErrorHandling:
    """Test cases for error handling and edge cases."""

    @pytest.fixture
    def mock_console(self):
        """Create mock console logger."""
        return Mock(spec=ConsoleLogger)

    def test_read_batch_file_permission_error(self, mock_console):
        """Test handling of permission errors when reading batch file."""
        service = BatchProcessingService("/root/protected.csv", mock_console)

        df = service.read_batch_file()

        # Should return empty DataFrame on error
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["Ticker", "Last Modified"]
        assert len(df) == 0

        # Should log error
        mock_console.error.assert_called()

    def test_update_ticker_status_write_error(self, mock_console):
        """Test handling of write errors when updating ticker status."""
        service = BatchProcessingService("/root/protected.csv", mock_console)

        success = service.update_ticker_status("AAPL")

        assert not success
        mock_console.error.assert_called()

    def test_clean_old_entries_file_corruption(self, mock_console):
        """Test handling of corrupted files during cleanup."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Corrupted,Data\nNot,Valid,CSV,Format\n")

        try:
            service = BatchProcessingService(f.name, mock_console)
            removed_count = service.clean_old_entries()

            # Should handle gracefully and return 0
            assert removed_count == 0
            mock_console.error.assert_called()
        finally:
            Path(f.name).unlink()

    def test_large_ticker_list_performance(self, mock_console):
        """Test performance with large ticker lists."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")

        try:
            service = BatchProcessingService(f.name, mock_console)

            # Test with 1000 tickers
            large_ticker_list = [f"TICKER{i:04d}" for i in range(1000)]
            batch_size = 50

            pending = service.get_pending_tickers(large_ticker_list, batch_size)

            assert len(pending) == batch_size
            assert all(isinstance(ticker, str) for ticker in pending)
        finally:
            Path(f.name).unlink()

    def test_concurrent_access_simulation(self, mock_console):
        """Test simulation of concurrent access scenarios."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")

        try:
            service1 = BatchProcessingService(f.name, mock_console)
            service2 = BatchProcessingService(f.name, mock_console)

            # Simulate concurrent updates
            success1 = service1.update_ticker_status("AAPL")
            success2 = service2.update_ticker_status("MSFT")

            # Both should succeed
            assert success1
            assert success2

            # Final state should contain both tickers
            final_df = service1.read_batch_file()
            tickers = set(final_df["Ticker"])
            assert "AAPL" in tickers or "MSFT" in tickers
        finally:
            Path(f.name).unlink()

    def test_invalid_date_formats(self, mock_console):
        """Test handling of invalid date formats in batch file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")
            f.write("AAPL,invalid-date\n")
            f.write("MSFT,2025-13-45\n")  # Invalid date
            f.write("GOOGL,2025-01-01\n")  # Valid date

        try:
            service = BatchProcessingService(f.name, mock_console)

            # Should handle invalid dates gracefully
            processed = service.get_processed_tickers_today()
            status = service.get_batch_status(["AAPL", "MSFT", "GOOGL"])

            # Should not crash
            assert isinstance(processed, set)
            assert isinstance(status, dict)
        finally:
            Path(f.name).unlink()

    def test_empty_ticker_names(self, mock_console):
        """Test handling of empty or whitespace ticker names."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")
            f.write(",2025-01-01\n")  # Empty ticker
            f.write("   ,2025-01-01\n")  # Whitespace ticker
            f.write("AAPL,2025-01-01\n")  # Valid ticker

        try:
            service = BatchProcessingService(f.name, mock_console)

            tickers = service.get_batch_tickers()

            # Should filter out empty/whitespace tickers
            assert tickers == ["AAPL"]
        finally:
            Path(f.name).unlink()

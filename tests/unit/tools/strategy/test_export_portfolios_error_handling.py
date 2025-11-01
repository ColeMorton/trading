"""
Unit tests for export_portfolios error handling.

Tests verify that export_portfolios properly handles and propagates
file system errors during portfolio export operations.
"""

import errno
from unittest.mock import Mock, patch

import pytest

from app.tools.strategy.export_portfolios import PortfolioExportError, export_portfolios


@pytest.mark.unit
class TestExportPortfoliosErrorHandling:
    """Test error handling in export_portfolios function."""

    @pytest.fixture
    def sample_portfolios(self):
        """Create sample portfolio data for testing."""
        return [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Score": 1.5,
                "Win Rate [%]": 65.0,
                "Total Trades": 100,
                "Profit Factor": 2.0,
                "Sortino Ratio": 1.5,
            }
        ]

    @pytest.fixture
    def export_config(self):
        """Create export configuration."""
        return {
            "TICKER": "AAPL",
            "STRATEGY_TYPES": ["SMA"],
            "STRATEGY_TYPE": "SMA",
            "BASE_DIR": "/tmp/test_exports",
            "USE_MA": True,
        }

    def test_export_directory_creation_failure(self, sample_portfolios, export_config):
        """Test handling of directory creation failures."""
        # Mock export_csv to raise OSError for directory creation
        with patch("app.tools.strategy.export_portfolios.export_csv") as mock_export:
            mock_export.side_effect = OSError(
                "Cannot create directory: Permission denied"
            )

            # export_portfolios wraps errors in PortfolioExportError
            with pytest.raises(PortfolioExportError) as exc_info:
                export_portfolios(
                    portfolios=sample_portfolios,
                    config=export_config,
                    export_type="portfolios",
                )

            assert "Cannot create directory" in str(exc_info.value)
            # Verify export_csv was called
            assert mock_export.call_count == 1

    def test_file_write_permission_error(self, sample_portfolios, export_config):
        """Test handling of file write permission errors."""
        # Mock export_csv to raise PermissionError
        with patch("app.tools.strategy.export_portfolios.export_csv") as mock_export:
            mock_export.side_effect = PermissionError(
                "Permission denied: /tmp/test_exports/portfolios.csv"
            )

            # export_portfolios wraps errors in PortfolioExportError
            with pytest.raises(PortfolioExportError) as exc_info:
                export_portfolios(
                    portfolios=sample_portfolios,
                    config=export_config,
                    export_type="portfolios",
                )

            assert "Permission denied" in str(exc_info.value)
            # Verify export_csv was called
            assert mock_export.call_count == 1

    def test_disk_space_exhaustion_handling(self, sample_portfolios, export_config):
        """Test handling of disk space exhaustion errors."""
        # Mock export_csv to raise OSError with ENOSPC (No space left on device)
        with patch("app.tools.strategy.export_portfolios.export_csv") as mock_export:
            no_space_error = OSError(errno.ENOSPC, "No space left on device")
            mock_export.side_effect = no_space_error

            # export_portfolios wraps errors in PortfolioExportError
            with pytest.raises(PortfolioExportError) as exc_info:
                export_portfolios(
                    portfolios=sample_portfolios,
                    config=export_config,
                    export_type="portfolios",
                )

            # Verify it contains the disk space error message
            assert "No space left on device" in str(exc_info.value)
            # Verify export_csv was called
            assert mock_export.call_count == 1

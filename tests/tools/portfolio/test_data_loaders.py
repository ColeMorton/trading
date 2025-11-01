"""Tests for portfolio data loading functions."""

from unittest.mock import MagicMock, patch

import pytest

from app.cli.models.portfolio import Direction, ReviewStrategyConfig, StrategyType
from app.tools.portfolio.data_loaders import load_strategies_from_raw_csv


@pytest.mark.integration
class TestLoadStrategiesFromRawCsv:
    """Test suite for load_strategies_from_raw_csv function."""

    @patch("app.tools.portfolio.data_loaders.Path")
    def test_load_strategies_file_not_found(self, mock_path):
        """Test error handling when CSV file doesn't exist."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        with pytest.raises(
            ValueError,
            match="(does not exist|Failed to load strategies)",
        ):
            load_strategies_from_raw_csv("nonexistent")

    @patch("app.tools.portfolio.data_loaders.Path")
    @patch("app.tools.portfolio.data_loaders.pl.read_csv")
    def test_load_strategies_read_csv_error(self, mock_read_csv, mock_path):
        """Test error handling when CSV reading fails."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        mock_read_csv.side_effect = Exception("CSV parsing error")

        with pytest.raises(ValueError, match="Failed to load strategies"):
            load_strategies_from_raw_csv("test_portfolio")

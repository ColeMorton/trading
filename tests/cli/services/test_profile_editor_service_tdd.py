#!/usr/bin/env python3
"""
TDD Test Suite for ProfileEditorService

This demonstrates unit testing the refactored service layer
created during the TDD REFACTOR phase.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.cli.services.profile_editor_service import ProfileEditorService


class TestProfileEditorServiceTDD:
    """Unit tests for ProfileEditorService following TDD principles."""

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock config manager."""
        mock_manager = Mock()
        mock_manager.profile_manager.profiles_dir = Path("/tmp/profiles")
        return mock_manager

    @pytest.fixture
    def editor_service(self, mock_config_manager):
        """Create ProfileEditorService instance."""
        return ProfileEditorService(mock_config_manager)

    @pytest.fixture
    def sample_profile(self):
        """Sample profile data for testing."""
        return {
            "metadata": {"name": "test_profile", "description": "Test profile"},
            "config_type": "strategy",
            "config": {
                "ticker": ["AAPL"],
                "strategy_types": ["SMA"],
                "minimums": {"win_rate": 0.5, "trades": 20},
            },
        }

    def test_load_profile_success(
        self, editor_service, mock_config_manager, sample_profile
    ):
        """Test successful profile loading."""
        mock_config_manager.profile_manager.load_profile.return_value = sample_profile

        result = editor_service.load_profile("test_profile")

        assert result == sample_profile
        mock_config_manager.profile_manager.load_profile.assert_called_once_with(
            "test_profile"
        )

    def test_load_profile_not_found(self, editor_service, mock_config_manager):
        """Test profile not found handling."""
        mock_config_manager.profile_manager.load_profile.side_effect = (
            FileNotFoundError()
        )

        with pytest.raises(FileNotFoundError, match="Profile 'test_profile' not found"):
            editor_service.load_profile("test_profile")

    def test_load_profile_invalid(self, editor_service, mock_config_manager):
        """Test invalid profile handling."""
        mock_config_manager.profile_manager.load_profile.side_effect = Exception(
            "Invalid YAML"
        )

        with pytest.raises(ValueError, match="Error loading profile: Invalid YAML"):
            editor_service.load_profile("test_profile")

    def test_set_field_value_ticker(self, editor_service, sample_profile):
        """Test setting ticker field value."""
        editor_service.set_field_value(sample_profile, "config.ticker", "MSFT,GOOGL")

        assert sample_profile["config"]["ticker"] == ["MSFT", "GOOGL"]

    def test_set_field_value_win_rate_valid(self, editor_service, sample_profile):
        """Test setting valid win rate."""
        editor_service.set_field_value(
            sample_profile, "config.minimums.win_rate", "0.75"
        )

        assert sample_profile["config"]["minimums"]["win_rate"] == 0.75

    def test_set_field_value_win_rate_invalid_high(
        self, editor_service, sample_profile
    ):
        """Test setting invalid win rate (too high)."""
        with pytest.raises(ValueError, match="win_rate must be between 0 and 1"):
            editor_service.set_field_value(
                sample_profile, "config.minimums.win_rate", "1.5"
            )

    def test_set_field_value_win_rate_invalid_low(self, editor_service, sample_profile):
        """Test setting invalid win rate (too low)."""
        with pytest.raises(ValueError, match="win_rate must be between 0 and 1"):
            editor_service.set_field_value(
                sample_profile, "config.minimums.win_rate", "-0.1"
            )

    def test_set_field_value_trades_valid(self, editor_service, sample_profile):
        """Test setting valid trades count."""
        editor_service.set_field_value(sample_profile, "config.minimums.trades", "50")

        assert sample_profile["config"]["minimums"]["trades"] == 50

    def test_set_field_value_trades_invalid(self, editor_service, sample_profile):
        """Test setting invalid trades count."""
        with pytest.raises(ValueError, match="trades must be non-negative"):
            editor_service.set_field_value(
                sample_profile, "config.minimums.trades", "-5"
            )

    def test_set_field_value_strategy_types(self, editor_service, sample_profile):
        """Test setting strategy types."""
        editor_service.set_field_value(
            sample_profile, "config.strategy_types", "SMA,EMA,MACD"
        )

        assert sample_profile["config"]["strategy_types"] == ["SMA", "EMA", "MACD"]

    def test_set_field_value_creates_nested_structure(
        self, editor_service, sample_profile
    ):
        """Test that setting field creates nested structure if needed."""
        editor_service.set_field_value(
            sample_profile, "config.new_section.new_field", "test_value"
        )

        assert sample_profile["config"]["new_section"]["new_field"] == "test_value"

    def test_get_editable_fields(self, editor_service, sample_profile):
        """Test extracting editable fields from profile."""
        fields = editor_service.get_editable_fields(sample_profile)

        expected_fields = [
            ("ticker", ["AAPL"]),
            ("strategy_types", ["SMA"]),
            ("minimums.win_rate", 0.5),
            ("minimums.trades", 20),
        ]

        assert fields == expected_fields

    def test_get_editable_fields_empty_config(self, editor_service):
        """Test extracting fields from empty config."""
        profile = {"metadata": {}, "config": {}}

        fields = editor_service.get_editable_fields(profile)

        assert fields == []

    def test_save_profile(self, editor_service, mock_config_manager, sample_profile):
        """Test saving profile."""
        editor_service.save_profile("test_profile", sample_profile)

        mock_config_manager.profile_manager.save_profile.assert_called_once_with(
            "test_profile", sample_profile
        )

    @patch("shutil.copy2")
    def test_create_backup(self, mock_copy, editor_service, mock_config_manager):
        """Test creating profile backup."""
        profiles_dir = Path("/tmp/profiles")
        mock_config_manager.profile_manager.profiles_dir = profiles_dir

        backup_path = editor_service.create_backup("test_profile")

        expected_backup = profiles_dir / "test_profile.yaml.backup"
        expected_source = profiles_dir / "test_profile.yaml"

        assert backup_path == expected_backup
        mock_copy.assert_called_once_with(expected_source, expected_backup)

    def test_convert_and_validate_value_string_field(self, editor_service):
        """Test converting unknown field as string."""
        result = editor_service._convert_and_validate_value(
            "custom_field", "test_value"
        )
        assert result == "test_value"

    def test_convert_and_validate_value_ticker_with_spaces(self, editor_service):
        """Test converting ticker field with spaces."""
        result = editor_service._convert_and_validate_value(
            "ticker", "AAPL, MSFT , GOOGL"
        )
        assert result == ["AAPL", "MSFT", "GOOGL"]

    def test_convert_and_validate_value_strategy_types_with_spaces(
        self, editor_service
    ):
        """Test converting strategy_types field with spaces."""
        result = editor_service._convert_and_validate_value(
            "strategy_types", "SMA, EMA , MACD"
        )
        assert result == ["SMA", "EMA", "MACD"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

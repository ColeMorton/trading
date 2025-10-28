#!/usr/bin/env python3
"""
TDD Test Suite for Profile Editing Functionality

This test demonstrates the Red-Green-Refactor TDD cycle for implementing
the profile editing functionality in the CLI config command.
"""

from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from app.cli.commands.config import app as config_app


class TestProfileEditingTDD:
    """Test class demonstrating TDD for profile editing functionality."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_profiles_dir(self):
        """Create temporary directory with test profiles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            profiles_dir = Path(temp_dir) / "profiles"
            profiles_dir.mkdir()

            # Create test profile
            test_profile = profiles_dir / "test_profile.yaml"
            test_profile.write_text(
                """
metadata:
  name: test_profile
  description: Test profile for editing

config_type: strategy
config:
  ticker: [AAPL]
  strategy_types: [SMA]
  minimums:
    win_rate: 0.5
    trades: 20
""",
            )

            yield profiles_dir

    # RED: Write failing tests first
    def test_edit_command_loads_existing_profile(self, cli_runner, temp_profiles_dir):
        """
        RED: Test that edit command can load an existing profile.
        This test should FAIL initially because the functionality is not implemented.
        """
        with patch("app.cli.commands.config.ConfigManager") as mock_config_manager:
            # Mock the config manager to use our temp directory
            mock_manager = Mock()
            mock_manager.profile_manager.profiles_dir = temp_profiles_dir
            mock_config_manager.return_value = mock_manager

            # Mock the profile loading
            mock_manager.profile_manager.load_profile.return_value = {
                "metadata": {
                    "name": "test_profile",
                    "description": "Test profile for editing",
                },
                "config_type": "strategy",
                "config": {
                    "ticker": ["AAPL"],
                    "strategy_types": ["SMA"],
                    "minimums": {"win_rate": 0.5, "trades": 20},
                },
            }

            # This should succeed when profile editing is properly implemented
            result = cli_runner.invoke(config_app, ["edit", "test_profile"])

            # These assertions will FAIL initially (RED phase)
            assert result.exit_code == 0, f"Command failed with output: {result.stdout}"
            assert "Profile loaded successfully" in result.stdout
            assert "test_profile" in result.stdout
            assert "Current configuration:" in result.stdout

    def test_edit_command_handles_nonexistent_profile(
        self, cli_runner, temp_profiles_dir,
    ):
        """
        RED: Test that edit command handles non-existent profile gracefully.
        This test should FAIL initially.
        """
        with patch("app.cli.commands.config.ConfigManager") as mock_config_manager:
            mock_manager = Mock()
            mock_manager.profile_manager.profiles_dir = temp_profiles_dir
            mock_config_manager.return_value = mock_manager

            # Mock profile not found
            mock_manager.profile_manager.load_profile.side_effect = FileNotFoundError(
                "Profile not found",
            )

            result = cli_runner.invoke(config_app, ["edit", "nonexistent_profile"])

            # These assertions will FAIL initially (RED phase)
            assert result.exit_code == 1
            assert "Profile 'nonexistent_profile' not found" in result.stdout

    def test_edit_command_allows_field_modification(
        self, cli_runner, temp_profiles_dir,
    ):
        """
        RED: Test that edit command allows modifying profile fields.
        This test should FAIL initially because editing is not implemented.
        """
        with patch("app.cli.commands.config.ConfigManager") as mock_config_manager:
            mock_manager = Mock()
            mock_manager.profile_manager.profiles_dir = temp_profiles_dir
            mock_config_manager.return_value = mock_manager

            # Mock the profile loading and saving
            original_profile = {
                "metadata": {"name": "test_profile", "description": "Test profile"},
                "config_type": "strategy",
                "config": {
                    "ticker": ["AAPL"],
                    "strategy_types": ["SMA"],
                    "minimums": {"win_rate": 0.5, "trades": 20},
                },
            }
            mock_manager.profile_manager.load_profile.return_value = original_profile

            # Test editing with field overrides
            result = cli_runner.invoke(
                config_app,
                [
                    "edit",
                    "test_profile",
                    "--set-field",
                    "config.ticker MSFT,GOOGL",
                    "--set-field",
                    "config.minimums.win_rate 0.6",
                ],
            )

            # These assertions will FAIL initially (RED phase)
            assert result.exit_code == 0
            assert "Profile updated successfully" in result.stdout
            mock_manager.profile_manager.save_profile.assert_called_once()

            # Verify the profile was updated correctly
            saved_call = mock_manager.profile_manager.save_profile.call_args
            updated_profile = saved_call[0][1]  # Second argument is the profile data
            assert updated_profile["config"]["ticker"] == ["MSFT", "GOOGL"]
            assert updated_profile["config"]["minimums"]["win_rate"] == 0.6

    def test_edit_command_validates_field_values(self, cli_runner, temp_profiles_dir):
        """
        RED: Test that edit command validates field values.
        This test should FAIL initially.
        """
        with patch("app.cli.commands.config.ConfigManager") as mock_config_manager:
            mock_manager = Mock()
            mock_manager.profile_manager.profiles_dir = temp_profiles_dir
            mock_config_manager.return_value = mock_manager

            profile = {
                "metadata": {"name": "test_profile"},
                "config_type": "strategy",
                "config": {"ticker": ["AAPL"], "minimums": {"win_rate": 0.5}},
            }
            mock_manager.profile_manager.load_profile.return_value = profile

            # Test invalid win rate
            result = cli_runner.invoke(
                config_app,
                [
                    "edit",
                    "test_profile",
                    "--set-field",
                    "config.minimums.win_rate 1.5",  # Invalid: > 1.0
                ],
            )

            # These assertions will FAIL initially (RED phase)
            assert result.exit_code == 1
            assert "Invalid value" in result.stdout
            assert "win_rate must be between 0 and 1" in result.stdout

    @pytest.mark.skip(
        reason="Interactive mode not yet implemented - TDD RED phase test",
    )
    def test_edit_command_shows_interactive_menu(self, cli_runner, temp_profiles_dir):
        """
        RED: Test that edit command shows interactive editing menu.
        This test should FAIL initially.
        """
        with patch("app.cli.commands.config.ConfigManager") as mock_config_manager:
            mock_manager = Mock()
            mock_manager.profile_manager.profiles_dir = temp_profiles_dir
            mock_config_manager.return_value = mock_manager

            profile = {
                "metadata": {"name": "test_profile"},
                "config_type": "strategy",
                "config": {"ticker": ["AAPL"], "strategy_types": ["SMA"]},
            }
            mock_manager.profile_manager.load_profile.return_value = profile

            # Mock interactive input
            with patch(
                "builtins.input", side_effect=["1", "MSFT,GOOGL", "5"],
            ):  # Select ticker, change value, exit
                result = cli_runner.invoke(
                    config_app, ["edit", "test_profile", "--interactive"],
                )

                # These assertions will FAIL initially (RED phase)
                assert result.exit_code == 0
                assert "Interactive Profile Editor" in result.stdout
                assert "[1] ticker" in result.stdout
                assert "[2] strategy_types" in result.stdout
                assert "[5] Save and exit" in result.stdout

    def test_edit_command_creates_backup_before_changes(
        self, cli_runner, temp_profiles_dir,
    ):
        """
        RED: Test that edit command creates backup before making changes.
        This test should FAIL initially.
        """
        with patch("app.cli.commands.config.ConfigManager") as mock_config_manager:
            mock_manager = Mock()
            mock_manager.profile_manager.profiles_dir = temp_profiles_dir
            mock_config_manager.return_value = mock_manager

            profile = {"metadata": {"name": "test_profile"}, "config": {}}
            mock_manager.profile_manager.load_profile.return_value = profile

            result = cli_runner.invoke(
                config_app,
                ["edit", "test_profile", "--set-field", "config.ticker AAPL"],
            )

            # These assertions will FAIL initially (RED phase)
            assert result.exit_code == 0
            assert "Backup created" in result.stdout

            # Verify backup was created
            backup_path = temp_profiles_dir / "test_profile.yaml.backup"
            assert backup_path.exists()


# This test runner will show all tests FAILING initially (RED phase)
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

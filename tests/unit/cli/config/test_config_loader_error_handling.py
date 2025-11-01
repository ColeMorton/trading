"""
Unit tests for ConfigLoader error handling.

Tests verify that ConfigLoader properly handles and propagates
errors during configuration loading from profiles.
"""

from unittest.mock import Mock, mock_open, patch

import pytest

from app.cli.config.loader import ConfigLoader
from app.cli.models.strategy import StrategyConfig


@pytest.mark.unit
class TestConfigLoaderErrorHandling:
    """Test error handling in ConfigLoader."""

    @pytest.fixture
    def config_loader(self):
        """Create ConfigLoader instance."""
        return ConfigLoader()

    def test_configuration_service_unavailable(self, config_loader):
        """Test handling of configuration service unavailability."""
        # Mock file operations to simulate service unavailability
        with patch("builtins.open") as mock_file:
            mock_file.side_effect = RuntimeError(
                "Configuration service unavailable: Connection refused"
            )

            # ConfigLoader wraps errors in ValueError
            with pytest.raises((RuntimeError, ValueError)) as exc_info:
                config_loader.load_from_profile(
                    profile_name="default_strategy",
                    config_type=StrategyConfig,
                )

            # Verify error message contains the original RuntimeError message
            assert "Configuration service unavailable" in str(exc_info.value)

    def test_corrupted_profile_file(self, config_loader):
        """Test handling of corrupted YAML profile files."""
        # Mock file with invalid YAML content
        invalid_yaml = "{ invalid: yaml: content: [unclosed"

        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            # ConfigLoader should raise an error for invalid YAML
            with pytest.raises(Exception) as exc_info:
                config_loader.load_from_profile(
                    profile_name="corrupted_profile",
                    config_type=StrategyConfig,
                )

            # Should be YAML parsing error or config validation error
            assert exc_info.value is not None

    def test_missing_profile_file(self, config_loader):
        """Test handling of missing profile files."""
        # Test with a truly nonexistent profile name
        # ConfigLoader should raise an error for missing profiles
        with pytest.raises((FileNotFoundError, ValueError, KeyError)) as exc_info:
            config_loader.load_from_profile(
                profile_name="this_profile_definitely_does_not_exist_12345",
                config_type=StrategyConfig,
            )

        # Verify error indicates the profile was not found
        error_msg = str(exc_info.value).lower()
        assert (
            "not found" in error_msg
            or "does not exist" in error_msg
            or "unknown" in error_msg
        )

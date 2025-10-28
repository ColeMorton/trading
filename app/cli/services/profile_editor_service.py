"""
Profile Editor Service

This service provides profile editing functionality with proper separation of concerns,
following TDD principles and clean architecture patterns.
"""

from pathlib import Path
import shutil
from typing import Any


class ProfileEditorService:
    """Service for editing configuration profiles with validation and backup."""

    def __init__(self, config_manager):
        """Initialize with config manager dependency."""
        self.config_manager = config_manager

    def load_profile(self, profile_name: str) -> dict[str, Any]:
        """
        Load profile data with proper error handling.

        Args:
            profile_name: Name of profile to load

        Returns:
            Profile data dictionary

        Raises:
            FileNotFoundError: If profile doesn't exist
            ValueError: If profile is invalid
        """
        try:
            return self.config_manager.profile_manager.load_profile(profile_name)
        except FileNotFoundError:
            msg = f"Profile '{profile_name}' not found"
            raise FileNotFoundError(msg)
        except Exception as e:
            msg = f"Error loading profile: {e}"
            raise ValueError(msg)

    def create_backup(self, profile_name: str) -> Path:
        """
        Create backup of profile before editing.

        Args:
            profile_name: Name of profile to backup

        Returns:
            Path to backup file
        """
        profiles_dir = self.config_manager.profile_manager.profiles_dir
        profile_path = profiles_dir / f"{profile_name}.yaml"
        backup_path = profiles_dir / f"{profile_name}.yaml.backup"

        shutil.copy2(profile_path, backup_path)
        return backup_path

    def set_field_value(
        self,
        profile_data: dict[str, Any],
        field_path: str,
        value: str,
    ) -> None:
        """
        Set field value with proper validation and type conversion.

        Args:
            profile_data: Profile data to modify
            field_path: Dot-separated field path (e.g., 'config.ticker')
            value: String value to set

        Raises:
            ValueError: If field path is invalid or value is invalid
        """
        path_parts = field_path.split(".")

        # Navigate to parent container
        current = profile_data
        for part in path_parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Set final field with validation
        final_field = path_parts[-1]
        current[final_field] = self._convert_and_validate_value(final_field, value)

    def _convert_and_validate_value(self, field_name: str, value: str) -> Any:
        """
        Convert string value to appropriate type with validation.

        Args:
            field_name: Name of the field
            value: String value to convert

        Returns:
            Converted and validated value

        Raises:
            ValueError: If value is invalid for field
        """
        if field_name == "ticker":
            return [t.strip() for t in value.split(",")]
        if field_name == "win_rate":
            float_value = float(value)
            if not 0 <= float_value <= 1:
                msg = "win_rate must be between 0 and 1"
                raise ValueError(msg)
            return float_value
        if field_name == "trades":
            int_value = int(value)
            if int_value < 0:
                msg = "trades must be non-negative"
                raise ValueError(msg)
            return int_value
        if field_name in ["strategy_types"]:
            return [t.strip() for t in value.split(",")]
        return value

    def save_profile(self, profile_name: str, profile_data: dict[str, Any]) -> None:
        """
        Save profile data.

        Args:
            profile_name: Name of profile to save
            profile_data: Profile data to save
        """
        self.config_manager.profile_manager.save_profile(profile_name, profile_data)

    def get_editable_fields(
        self,
        profile_data: dict[str, Any],
    ) -> list[tuple[str, Any]]:
        """
        Extract editable fields from profile data.

        Args:
            profile_data: Profile data to analyze

        Returns:
            List of (field_name, current_value) tuples
        """
        config_data = profile_data.get("config", {})
        editable_fields = []

        if "ticker" in config_data:
            editable_fields.append(("ticker", config_data["ticker"]))
        if "strategy_types" in config_data:
            editable_fields.append(("strategy_types", config_data["strategy_types"]))
        if "minimums" in config_data:
            for key, value in config_data["minimums"].items():
                editable_fields.append((f"minimums.{key}", value))

        return editable_fields

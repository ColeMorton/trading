"""
Configuration and profile management system.

This module provides the core functionality for managing YAML-based
configuration profiles with inheritance and validation.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from ..models.base import BaseConfig
from .profiles import Profile, ProfileConfig, ProfileMetadata


class ProfileManager:
    """Manages configuration profiles with inheritance and validation."""

    def __init__(self, config: ProfileConfig | None = None):
        """Initialize the profile manager.

        Args:
            config: Profile management configuration
        """
        self.config = config or ProfileConfig()
        self._cache: dict[str, Profile] = {}

    @property
    def profiles_dir(self) -> Path:
        """Get the profiles directory."""
        return self.config.profiles_dir

    @profiles_dir.setter
    def profiles_dir(self, value: Path) -> None:
        """Set the profiles directory."""
        self.config.profiles_dir = value

    @profiles_dir.deleter
    def profiles_dir(self) -> None:
        """Delete the profiles directory (for test cleanup)."""
        pass

    def list_profiles(self) -> list[str]:
        """List all available profile names (searches recursively)."""
        if not self.profiles_dir.exists():
            return []

        profiles = []
        # Search recursively for YAML files in subdirectories
        for file_path in self.profiles_dir.rglob("*.yaml"):
            if file_path.stem not in [
                "config",
                "defaults",
                "README",
            ]:  # Skip system files
                profiles.append(file_path.stem)

        return sorted(profiles)

    def profile_exists(self, name: str) -> bool:
        """Check if a profile exists (searches recursively)."""
        if not self.profiles_dir.exists():
            return False

        # Search recursively for the profile
        for _file_path in self.profiles_dir.rglob(f"{name}.yaml"):
            return True
        return False

    def load_profile(self, name: str, use_cache: bool = True) -> Profile:
        """Load a profile by name (searches recursively).

        Args:
            name: Profile name
            use_cache: Whether to use cached profiles

        Returns:
            Loaded profile

        Raises:
            FileNotFoundError: If profile doesn't exist
            ValidationError: If profile is invalid
        """
        if use_cache and name in self._cache:
            return self._cache[name]

        # Search recursively for the profile with priority order
        profile_path = None

        # Priority search paths (portfolio_review takes priority over concurrency)
        priority_paths = [
            "portfolio_review/portfolios",
            "portfolio_review/single",
            "portfolio_review/multi",
            "portfolio_review/templates",
            "strategy",
            "concurrency",
        ]

        # First try priority paths
        for priority_dir in priority_paths:
            search_path = self.profiles_dir / priority_dir / f"{name}.yaml"
            if search_path.exists():
                profile_path = search_path
                break

        # If not found in priority paths, do general recursive search
        if not profile_path:
            for file_path in self.profiles_dir.rglob(f"{name}.yaml"):
                profile_path = file_path
                break

        if not profile_path:
            msg = f"Profile '{name}' not found"
            raise FileNotFoundError(msg)

        try:
            with open(profile_path) as f:
                content = f.read()

            profile = Profile.from_yaml(content)

            # Skip validation for template profiles or profiles with portfolio_reference
            if not profile.metadata.is_template and not (
                profile.config_type == "portfolio_review"
                and "portfolio_reference" in profile.config
            ):
                profile.validate_config()

            if use_cache:
                self._cache[name] = profile

            return profile

        except yaml.YAMLError as e:
            msg = f"Invalid YAML in profile '{name}': {e}"
            raise ValueError(msg)
        except Exception as e:
            msg = f"Error loading profile '{name}': {e}"
            raise ValueError(msg)

    def save_profile(self, profile: Profile, name: str | None = None) -> Path:
        """Save a profile to disk.

        Args:
            profile: Profile to save
            name: Profile name (defaults to profile metadata name)

        Returns:
            Path to saved profile file
        """
        if name is None:
            name = profile.metadata.name

        # Update timestamp
        profile.update_timestamp()

        # Create backup if profile exists
        profile_path = self.profiles_dir / f"{name}.yaml"
        if profile_path.exists() and self.config.backup_count > 0:
            self._create_backup(profile_path)

        # Save profile
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        with open(profile_path, "w") as f:
            f.write(profile.to_yaml())

        # Update cache
        self._cache[name] = profile

        return profile_path

    def delete_profile(self, name: str) -> bool:
        """Delete a profile.

        Args:
            name: Profile name to delete

        Returns:
            True if deleted, False if not found
        """
        profile_path = self.profiles_dir / f"{name}.yaml"
        if not profile_path.exists():
            return False

        # Create backup before deletion
        if self.config.backup_count > 0:
            self._create_backup(profile_path, suffix=".deleted")

        profile_path.unlink()

        # Remove from cache
        if name in self._cache:
            del self._cache[name]

        return True

    def resolve_inheritance(self, profile: Profile) -> dict[str, Any]:
        """Resolve profile inheritance chain and return merged configuration.

        Args:
            profile: Profile to resolve

        Returns:
            Merged configuration dictionary

        Raises:
            ValidationError: If inheritance chain is invalid
        """
        if profile.inherits_from is None:
            merged_config = profile.config.copy()
        else:
            # Prevent circular inheritance
            visited = set()
            inheritance_chain: list[str] = []
            current = profile

            while current.inherits_from is not None:
                if current.metadata.name in visited:
                    msg = f"Circular inheritance detected: {' -> '.join(inheritance_chain)}"
                    raise ValidationError(
                        msg,
                        Profile,
                    )

                visited.add(current.metadata.name)
                inheritance_chain.append(current.metadata.name)

                try:
                    current = self.load_profile(current.inherits_from)
                except FileNotFoundError as e:
                    msg = f"Parent profile '{current.inherits_from}' not found"
                    raise FileNotFoundError(msg) from e

            # Merge configurations from parent to child
            merged_config = current.config.copy()

            # Walk back through inheritance chain
            for profile_name in reversed(inheritance_chain):
                if profile_name == profile.metadata.name:
                    child_profile = profile
                else:
                    child_profile = self.load_profile(profile_name)

                merged_config = self._merge_configs(merged_config, child_profile.config)

        # Resolve portfolio_reference if present (for portfolio_review configs)
        if (
            profile.config_type == "portfolio_review"
            and "portfolio_reference" in merged_config
        ):
            merged_config = self._resolve_portfolio_reference(merged_config)

        return merged_config

    def create_profile(
        self,
        name: str,
        config_type: str,
        config: dict[str, Any],
        description: str | None = None,
        inherits_from: str | None = None,
        tags: list[str] | None = None,
        author: str | None = None,
    ) -> Profile:
        """Create a new profile.

        Args:
            name: Profile name
            config_type: Type of configuration
            config: Configuration data
            description: Profile description
            inherits_from: Parent profile name
            tags: Profile tags
            author: Profile author

        Returns:
            Created profile
        """
        metadata = ProfileMetadata(
            name=name,
            description=description,
            tags=tags or [],
            author=author,
        )

        profile = Profile(
            metadata=metadata,
            inherits_from=inherits_from,
            config_type=config_type,
            config=config,
        )

        # Validate configuration
        profile.validate_config()

        return profile

    def _create_backup(self, file_path: Path, suffix: str = ".bak") -> None:
        """Create a backup of a profile file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = (
            file_path.parent / f"{file_path.stem}_{timestamp}{suffix}{file_path.suffix}"
        )

        shutil.copy2(file_path, backup_path)

        # Clean up old backups
        self._cleanup_backups(file_path)

    def _cleanup_backups(self, file_path: Path) -> None:
        """Clean up old backup files."""
        if self.config.backup_count <= 0:
            return

        pattern = f"{file_path.stem}_*{file_path.suffix}"
        backups = list(file_path.parent.glob(pattern))
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Keep only the most recent backups
        for backup in backups[self.config.backup_count :]:
            backup.unlink()

    def _resolve_portfolio_reference(self, config: dict[str, Any]) -> dict[str, Any]:
        """Resolve portfolio_reference by loading strategies from referenced portfolio file.

        Args:
            config: Configuration dictionary that may contain portfolio_reference

        Returns:
            Configuration with strategies merged from referenced portfolio file
        """
        portfolio_reference = config.get("portfolio_reference")
        if not portfolio_reference:
            return config

        from pathlib import Path

        import yaml

        # Resolve portfolio reference path relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        portfolio_path = project_root / portfolio_reference

        if not portfolio_path.exists():
            msg = f"Portfolio reference file not found: {portfolio_path}"
            raise ValidationError(
                msg,
                Profile,
            )

        try:
            with open(portfolio_path) as f:
                portfolio_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            msg = f"Invalid YAML in portfolio reference {portfolio_path}: {e}"
            raise ValidationError(
                msg,
                Profile,
            )

        # Extract strategies from the referenced portfolio
        strategies = portfolio_data.get("strategies", [])
        if not strategies:
            msg = f"No strategies found in portfolio reference: {portfolio_path}"
            raise ValidationError(
                msg,
                Profile,
            )

        # Create a copy of config and merge in the strategies
        resolved_config = config.copy()
        resolved_config["strategies"] = strategies

        # Remove the portfolio_reference as it's been resolved
        resolved_config.pop("portfolio_reference", None)

        return resolved_config

    def _merge_configs(
        self,
        base: dict[str, Any],
        override: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge two configuration dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result


class ConfigManager:
    """High-level configuration management interface."""

    def __init__(self, profile_config: ProfileConfig | None = None):
        """Initialize the configuration manager.

        Args:
            profile_config: Profile management configuration
        """
        self.profile_manager = ProfileManager(profile_config)
        self._default_profile: str | None = None

    def get_default_profile(self) -> str | None:
        """Get the default profile name."""
        if self._default_profile:
            return self._default_profile

        # Try to load from config file
        config_path = self.profile_manager.profiles_dir / "config.yaml"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                return config.get("default_profile")
            except Exception:
                pass

        return None

    def set_default_profile(self, name: str) -> None:
        """Set the default profile name."""
        if not self.profile_manager.profile_exists(name):
            msg = f"Profile '{name}' does not exist"
            raise ValueError(msg)

        self._default_profile = name

        # Save to config file
        config_path = self.profile_manager.profiles_dir / "config.yaml"
        config = {"default_profile": name}

        with open(config_path, "w") as f:
            yaml.dump(config, f)

    def load_config(
        self,
        profile_name: str | None = None,
        config_overrides: dict[str, Any] | None = None,
    ) -> BaseConfig:
        """Load and validate configuration.

        Args:
            profile_name: Profile name (uses default if None)
            config_overrides: Configuration overrides

        Returns:
            Validated configuration
        """
        if profile_name is None:
            profile_name = self.get_default_profile()

        if profile_name is None:
            msg = "No profile specified and no default profile set"
            raise ValueError(msg)

        # Load profile
        profile = self.profile_manager.load_profile(profile_name)

        # Resolve inheritance
        config_dict = self.profile_manager.resolve_inheritance(profile)

        # Apply overrides
        if config_overrides:
            config_dict = self.profile_manager._merge_configs(
                config_dict,
                config_overrides,
            )

        # Get appropriate model and validate
        model_class = profile.get_config_model()
        return model_class(**config_dict)

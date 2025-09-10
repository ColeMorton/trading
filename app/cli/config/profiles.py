"""
Profile models and management for YAML-based configuration.

This module defines the structure for configuration profiles and provides
functionality for profile inheritance and validation.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, validator

from ..models.base import BaseConfig
from ..models.concurrency import ConcurrencyAnalysisConfig, ConcurrencyConfig
from ..models.portfolio import (
    PortfolioConfig,
    PortfolioProcessingConfig,
    PortfolioSynthesisConfig,
)
from ..models.spds import SPDSConfig
from ..models.strategy import MACDConfig, MACrossConfig, StrategyConfig


class ProfileMetadata(BaseModel):
    """Metadata for configuration profiles."""

    name: str = Field(description="Profile name")
    description: Optional[str] = Field(default=None, description="Profile description")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )
    version: str = Field(default="1.0", description="Profile version")
    tags: List[str] = Field(
        default_factory=list, description="Profile tags for organization"
    )
    author: Optional[str] = Field(default=None, description="Profile author")
    is_template: bool = Field(
        default=False, description="Whether this is a base template profile"
    )


class Profile(BaseModel):
    """A configuration profile with metadata and inheritance support."""

    metadata: ProfileMetadata = Field(description="Profile metadata")
    inherits_from: Optional[str] = Field(
        default=None, description="Parent profile name"
    )
    config_type: str = Field(
        description="Type of configuration (strategy, portfolio, concurrency)"
    )
    config: Dict[str, Any] = Field(description="Configuration data")

    @validator("config_type")
    def validate_config_type(cls, v):
        """Validate config type is supported."""
        valid_types = {
            "base",
            "strategy",
            "ma_cross",
            "macd",
            "portfolio",
            "portfolio_processing",
            "portfolio_review",
            "concurrency",
            "concurrency_analysis",
            "spds",
        }
        if v not in valid_types:
            raise ValueError(f"Config type must be one of: {', '.join(valid_types)}")
        return v

    def get_config_model(self) -> BaseModel:
        """Get the appropriate Pydantic model for this profile's config type."""
        model_map = {
            "base": BaseConfig,
            "strategy": StrategyConfig,
            "ma_cross": MACrossConfig,
            "macd": MACDConfig,
            "portfolio": PortfolioConfig,
            "portfolio_processing": PortfolioProcessingConfig,
            "portfolio_synthesis": PortfolioSynthesisConfig,
            "portfolio_review": PortfolioSynthesisConfig,  # Backward compatibility
            "concurrency": ConcurrencyConfig,
            "concurrency_analysis": ConcurrencyAnalysisConfig,
            "spds": SPDSConfig,
        }
        return model_map[self.config_type]

    def validate_config(self) -> BaseModel:
        """Validate the configuration using the appropriate Pydantic model."""
        model_class = self.get_config_model()
        return model_class(**self.config)

    def to_yaml(self) -> str:
        """Convert profile to YAML string."""
        # Convert to dict and handle datetime serialization
        profile_dict = self.dict()
        profile_dict["metadata"]["created_at"] = self.metadata.created_at.isoformat()
        profile_dict["metadata"]["updated_at"] = self.metadata.updated_at.isoformat()

        return yaml.dump(profile_dict, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "Profile":
        """Create profile from YAML string."""
        data = yaml.safe_load(yaml_content)

        # Handle datetime parsing
        if "metadata" in data:
            if "created_at" in data["metadata"]:
                data["metadata"]["created_at"] = datetime.fromisoformat(
                    data["metadata"]["created_at"]
                )
            if "updated_at" in data["metadata"]:
                data["metadata"]["updated_at"] = datetime.fromisoformat(
                    data["metadata"]["updated_at"]
                )

        return cls(**data)

    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.metadata.updated_at = datetime.now()


class ProfileConfig(BaseModel):
    """Configuration for the profile management system."""

    profiles_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "profiles",
        description="Directory containing profile files",
    )
    default_profile: Optional[str] = Field(
        default=None, description="Default profile name to use"
    )
    auto_save: bool = Field(
        default=True, description="Automatically save profile changes"
    )
    backup_count: int = Field(
        default=5, ge=0, description="Number of backup copies to keep"
    )

    @validator("profiles_dir", pre=True)
    def validate_profiles_dir(cls, v):
        """Ensure profiles directory exists."""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v.resolve()

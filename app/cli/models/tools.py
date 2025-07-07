"""
Tools configuration models.

This module defines Pydantic models for tools commands configuration.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from .base import BaseConfig


class SchemaConfig(BaseConfig):
    """Configuration for schema operations."""

    file_path: Optional[str] = Field(
        None, description="Path to file for schema detection/conversion"
    )
    target_schema: str = Field(
        "extended", description="Target schema type: base, extended, filtered"
    )
    validate_only: bool = Field(False, description="Only validate, don't convert")
    strict_mode: bool = Field(True, description="Strict validation mode")
    output_file: Optional[str] = Field(
        None, description="Output file path for conversions"
    )


class ValidationConfig(BaseConfig):
    """Configuration for data validation."""

    file_paths: List[str] = Field(
        default_factory=list, description="List of file paths to validate"
    )
    directory: Optional[str] = Field(
        None, description="Directory to validate all CSV files"
    )
    schema_validation: bool = Field(True, description="Enable schema validation")
    data_validation: bool = Field(True, description="Enable data content validation")
    strict_mode: bool = Field(False, description="Strict validation mode")
    output_format: str = Field(
        "table", description="Output format: table, json, summary"
    )
    save_report: Optional[str] = Field(
        None, description="Save validation report to file"
    )


class HealthConfig(BaseConfig):
    """Configuration for system health checks."""

    check_files: bool = Field(True, description="Check file system health")
    check_dependencies: bool = Field(True, description="Check Python dependencies")
    check_data: bool = Field(True, description="Check data integrity")
    check_config: bool = Field(True, description="Check configuration validity")
    check_performance: bool = Field(False, description="Run performance checks")
    output_format: str = Field(
        "table", description="Output format: table, json, summary"
    )
    save_report: Optional[str] = Field(None, description="Save health report to file")

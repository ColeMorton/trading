"""
API Migration Strategy

This module provides tools and utilities for managing API version migrations,
including deprecation notices, migration paths, and compatibility layers.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from fastapi import Request, Response
from pydantic import BaseModel

from app.api.versioning import APIVersion, version_manager


@dataclass
class MigrationStep:
    """Represents a single step in an API migration."""

    step_id: str
    description: str
    required: bool
    automated: bool = False
    migration_function: Optional[Callable] = None


@dataclass
class MigrationPath:
    """Defines a migration path between API versions."""

    from_version: APIVersion
    to_version: APIVersion
    steps: List[MigrationStep]
    estimated_effort: str  # "low", "medium", "high"
    breaking_changes: List[str]
    deprecated_features: List[str]
    new_features: List[str]


class MigrationPlanner:
    """Plans and manages API version migrations."""

    def __init__(self):
        self.migration_paths: Dict[tuple, MigrationPath] = {}
        self.deprecation_warnings: Dict[str, str] = {}
        self._setup_default_migrations()

    def _setup_default_migrations(self):
        """Set up default migration paths."""
        # Future: When v2 is added, create migration path from v1 to v2
        pass

    def add_migration_path(self, migration_path: MigrationPath):
        """Add a new migration path."""
        key = (migration_path.from_version, migration_path.to_version)
        self.migration_paths[key] = migration_path

    def get_migration_path(
        self, from_version: APIVersion, to_version: APIVersion
    ) -> Optional[MigrationPath]:
        """Get migration path between two versions."""
        return self.migration_paths.get((from_version, to_version))

    def plan_deprecation(
        self,
        version: APIVersion,
        deprecation_date: datetime,
        sunset_date: datetime,
        migration_guide_url: str,
    ):
        """Plan deprecation for a version."""
        version_manager.deprecate_version(
            version=version,
            sunset_date=sunset_date,
            migration_guide_url=migration_guide_url,
        )

    def get_deprecation_timeline(self, version: APIVersion) -> Dict[str, Any]:
        """Get deprecation timeline for a version."""
        info = version_manager.get_version_info(version)

        timeline = {
            "version": version.value,
            "current_status": info.status.value,
            "introduced": info.introduced.isoformat(),
        }

        if info.deprecated_date:
            timeline["deprecated_date"] = info.deprecated_date.isoformat()
            timeline["days_deprecated"] = (
                datetime.utcnow() - info.deprecated_date
            ).days

        if info.sunset_date:
            timeline["sunset_date"] = info.sunset_date.isoformat()
            timeline["days_until_sunset"] = (info.sunset_date - datetime.utcnow()).days

            # Add urgency level
            days_left = timeline["days_until_sunset"]
            if days_left <= 30:
                timeline["urgency"] = "critical"
            elif days_left <= 90:
                timeline["urgency"] = "high"
            elif days_left <= 180:
                timeline["urgency"] = "medium"
            else:
                timeline["urgency"] = "low"

        return timeline


class CompatibilityLayer:
    """Provides compatibility between API versions."""

    def __init__(self):
        self.transformers: Dict[tuple, Callable] = {}
        self.response_adapters: Dict[tuple, Callable] = {}

    def add_request_transformer(
        self,
        from_version: APIVersion,
        to_version: APIVersion,
        transformer: Callable[[Dict], Dict],
    ):
        """Add a request transformer between versions."""
        self.transformers[(from_version, to_version)] = transformer

    def add_response_adapter(
        self,
        from_version: APIVersion,
        to_version: APIVersion,
        adapter: Callable[[Dict], Dict],
    ):
        """Add a response adapter between versions."""
        self.response_adapters[(from_version, to_version)] = adapter

    def transform_request(
        self, request_data: Dict, from_version: APIVersion, to_version: APIVersion
    ) -> Dict:
        """Transform request data between versions."""
        transformer = self.transformers.get((from_version, to_version))
        if transformer:
            return transformer(request_data)
        return request_data

    def adapt_response(
        self, response_data: Dict, from_version: APIVersion, to_version: APIVersion
    ) -> Dict:
        """Adapt response data between versions."""
        adapter = self.response_adapters.get((from_version, to_version))
        if adapter:
            return adapter(response_data)
        return response_data


class MigrationGuide:
    """Generates migration guides and documentation."""

    def __init__(self, planner: MigrationPlanner):
        self.planner = planner

    def generate_migration_guide(
        self, from_version: APIVersion, to_version: APIVersion
    ) -> Dict[str, Any]:
        """Generate a comprehensive migration guide."""
        migration_path = self.planner.get_migration_path(from_version, to_version)

        if not migration_path:
            return {
                "error": f"No migration path found from {from_version.value} to {to_version.value}"
            }

        guide = {
            "migration": {
                "from_version": from_version.value,
                "to_version": to_version.value,
                "estimated_effort": migration_path.estimated_effort,
                "total_steps": len(migration_path.steps),
            },
            "breaking_changes": migration_path.breaking_changes,
            "deprecated_features": migration_path.deprecated_features,
            "new_features": migration_path.new_features,
            "migration_steps": [
                {
                    "step": i + 1,
                    "id": step.step_id,
                    "description": step.description,
                    "required": step.required,
                    "automated": step.automated,
                }
                for i, step in enumerate(migration_path.steps)
            ],
            "timeline": self.planner.get_deprecation_timeline(from_version),
            "resources": {
                "documentation": f"/docs/api/migration/{from_version.value}-to-{to_version.value}",
                "examples": f"/docs/api/examples/{to_version.value}",
                "changelog": f"/docs/api/changelog/{to_version.value}",
                "support": "/docs/api/support",
            },
        }

        return guide

    def generate_deprecation_notice(self, version: APIVersion) -> Dict[str, Any]:
        """Generate a deprecation notice."""
        timeline = self.planner.get_deprecation_timeline(version)

        notice = {
            "deprecated_version": version.value,
            "status": timeline.get("current_status"),
            "message": f"API version {version.value} is deprecated",
            "timeline": timeline,
            "recommended_action": "Migrate to the latest stable version",
            "migration_resources": {
                "guide": f"/docs/api/migration/{version.value}-to-latest",
                "support": "/docs/api/support",
            },
        }

        # Add urgency-specific messaging
        urgency = timeline.get("urgency", "low")
        if urgency == "critical":
            notice[
                "message"
            ] = f"⚠️ URGENT: API version {version.value} will be sunset soon!"
            notice[
                "recommended_action"
            ] = "Migrate immediately to avoid service disruption"
        elif urgency == "high":
            notice[
                "message"
            ] = f"⚠️ WARNING: API version {version.value} is being deprecated"
            notice["recommended_action"] = "Plan migration as soon as possible"

        return notice


# Global instances
migration_planner = MigrationPlanner()
compatibility_layer = CompatibilityLayer()
migration_guide = MigrationGuide(migration_planner)


# Example usage and setup for future versions
def setup_future_migrations():
    """Set up migrations for future API versions (example for when v2 is introduced)."""

    # Example: When v2 is introduced, this would be the migration path from v1 to v2
    # v1_to_v2 = MigrationPath(
    #     from_version=APIVersion.V1,
    #     to_version=APIVersion.V2,
    #     steps=[
    #         MigrationStep(
    #             step_id="update_endpoints",
    #             description="Update endpoint URLs to use new naming conventions",
    #             required=True
    #         ),
    #         MigrationStep(
    #             step_id="update_request_format",
    #             description="Update request body format for portfolio creation",
    #             required=True
    #         ),
    #         MigrationStep(
    #             step_id="update_auth",
    #             description="Migrate to new authentication system",
    #             required=True
    #         )
    #     ],
    #     estimated_effort="medium",
    #     breaking_changes=[
    #         "Portfolio creation endpoint changed from POST /portfolios to POST /portfolio-collections",
    #         "Authentication now requires JWT tokens instead of API keys"
    #     ],
    #     deprecated_features=[
    #         "Legacy authentication with API keys",
    #         "CSV export format v1"
    #     ],
    #     new_features=[
    #         "Real-time portfolio updates via WebSocket",
    #         "Advanced filtering and sorting",
    #         "Batch operations support"
    #     ]
    # )
    # migration_planner.add_migration_path(v1_to_v2)
    pass


# Initialize future migrations setup
setup_future_migrations()

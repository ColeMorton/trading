"""
Config command service for executing configuration management commands.
"""

from typing import Any

from ...models.schemas import (
    ConfigEditRequest,
    ConfigListRequest,
    ConfigSetDefaultRequest,
    ConfigShowRequest,
    ConfigValidateRequest,
    ConfigVerifyDefaultsRequest,
)
from ..base import BaseCommandService


class ConfigService(BaseCommandService):
    """Service for executing config commands."""

    async def execute_list(self, params: ConfigListRequest) -> dict[str, Any]:
        """
        Execute config list command.

        Args:
            params: Config list parameters

        Returns:
            Command result dictionary
        """
        await self.update_progress(10, "Loading profiles...")

        command = params.to_cli_args()

        await self.update_progress(50, "Retrieving profile list...")

        result = await self.execute_cli_command(command, timeout=30)

        await self.update_progress(90, "Formatting results...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get(
                "error",
                "Unknown error occurred",
            )
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            msg = f"{error_type}: {error_msg}"
            raise RuntimeError(msg)

        await self.update_progress(100, "Profile list retrieved")

        return {
            "success": True,
            "output": result["stdout"],
        }

    async def execute_show(self, params: ConfigShowRequest) -> dict[str, Any]:
        """Execute config show command."""
        await self.update_progress(10, "Loading profile configuration...")

        command = params.to_cli_args()

        await self.update_progress(50, f"Retrieving profile: {params.profile_name}...")

        result = await self.execute_cli_command(command, timeout=30)

        await self.update_progress(90, "Formatting configuration...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get(
                "error",
                "Unknown error occurred",
            )
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            msg = f"{error_type}: {error_msg}"
            raise RuntimeError(msg)

        await self.update_progress(100, "Profile configuration retrieved")

        return {
            "success": True,
            "profile_name": params.profile_name,
            "output": result["stdout"],
        }

    async def execute_verify_defaults(
        self,
        params: ConfigVerifyDefaultsRequest,
    ) -> dict[str, Any]:
        """Execute config verify-defaults command."""
        await self.update_progress(10, "Verifying default profiles...")

        command = params.to_cli_args()

        await self.update_progress(50, "Checking default profiles...")

        result = await self.execute_cli_command(command, timeout=30)

        await self.update_progress(90, "Processing verification results...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get(
                "error",
                "Unknown error occurred",
            )
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            msg = f"{error_type}: {error_msg}"
            raise RuntimeError(msg)

        await self.update_progress(100, "Default profiles verified")

        return {
            "success": True,
            "output": result["stdout"],
        }

    async def execute_set_default(
        self,
        params: ConfigSetDefaultRequest,
    ) -> dict[str, Any]:
        """Execute config set-default command."""
        await self.update_progress(10, "Setting default profile...")

        command = params.to_cli_args()

        await self.update_progress(50, f"Setting {params.profile_name} as default...")

        result = await self.execute_cli_command(command, timeout=30)

        await self.update_progress(90, "Updating configuration...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get(
                "error",
                "Unknown error occurred",
            )
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            msg = f"{error_type}: {error_msg}"
            raise RuntimeError(msg)

        await self.update_progress(100, "Default profile set")

        return {
            "success": True,
            "profile_name": params.profile_name,
            "output": result["stdout"],
        }

    async def execute_edit(self, params: ConfigEditRequest) -> dict[str, Any]:
        """Execute config edit command."""
        await self.update_progress(10, "Loading profile for editing...")

        command = params.to_cli_args()

        await self.update_progress(50, f"Editing profile: {params.profile_name}...")

        result = await self.execute_cli_command(command, timeout=60)

        await self.update_progress(90, "Saving changes...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get(
                "error",
                "Unknown error occurred",
            )
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            msg = f"{error_type}: {error_msg}"
            raise RuntimeError(msg)

        await self.update_progress(100, "Profile edited successfully")

        return {
            "success": True,
            "profile_name": params.profile_name,
            "output": result["stdout"],
        }

    async def execute_validate(self, params: ConfigValidateRequest) -> dict[str, Any]:
        """Execute config validate command."""
        await self.update_progress(10, "Initializing validation...")

        command = params.to_cli_args()

        target = params.profile_name if params.profile_name else "all profiles"
        await self.update_progress(50, f"Validating {target}...")

        result = await self.execute_cli_command(command, timeout=60)

        await self.update_progress(90, "Processing validation results...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get(
                "error",
                "Unknown error occurred",
            )
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            msg = f"{error_type}: {error_msg}"
            raise RuntimeError(msg)

        await self.update_progress(100, "Validation complete")

        return {
            "success": True,
            "profile_name": params.profile_name,
            "output": result["stdout"],
        }

"""
Strategy command service for executing strategy analysis commands.
"""

from typing import Any

from ...models.schemas import (
    SectorCompareRequest,
    StrategyReviewRequest,
    StrategyRunRequest,
    StrategySweepRequest,
)
from ..base import BaseCommandService


class StrategyService(BaseCommandService):
    """Service for executing strategy commands."""

    async def execute_run(self, params: StrategyRunRequest) -> dict[str, Any]:
        """
        Execute strategy run command.

        Args:
            params: Strategy run parameters

        Returns:
            Command result dictionary
        """
        await self.update_progress(10, "Initializing strategy analysis...")

        # Build CLI command
        command = params.to_cli_args()

        await self.update_progress(30, "Fetching market data...")

        # Execute command
        result = await self.execute_cli_command(command, timeout=600)

        await self.update_progress(80, "Processing results...")

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

        await self.update_progress(100, "Strategy analysis complete")

        return {
            "success": True,
            "ticker": params.ticker,
            "strategy_type": params.strategy_type,
            "fast_period": params.fast_period,
            "slow_period": params.slow_period,
            "output": result["stdout"],
        }

    async def execute_sweep(self, params: StrategySweepRequest) -> dict[str, Any]:
        """
        Execute strategy parameter sweep.

        Args:
            params: Sweep parameters

        Returns:
            Command result dictionary
        """
        await self.update_progress(5, "Initializing parameter sweep...")

        command = params.to_cli_args()

        await self.update_progress(15, "Fetching market data...")
        await self.update_progress(30, "Testing parameter combinations...")

        # Execute command (longer timeout for sweep)
        result = await self.execute_cli_command(command, timeout=1800)

        await self.update_progress(90, "Processing sweep results...")

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

        await self.update_progress(100, "Parameter sweep complete")

        # Extract sweep_run_id from CLI output if database persistence was used
        sweep_run_id = None
        output = result["stdout"]

        # Look for "run ID: xxxxxxxx..." pattern in output
        import re

        run_id_match = re.search(r"run ID: ([a-f0-9]{8})", output)
        if run_id_match:
            sweep_run_id = run_id_match.group(1)

        return {
            "success": True,
            "ticker": params.ticker,
            "output": output,
            "sweep_run_id": sweep_run_id,  # Include sweep_run_id if found
        }

    async def execute_review(self, params: StrategyReviewRequest) -> dict[str, Any]:
        """
        Execute strategy review.

        Args:
            params: Review parameters

        Returns:
            Command result dictionary
        """
        await self.update_progress(10, "Initializing strategy review...")

        command = params.to_cli_args()

        await self.update_progress(30, "Analyzing strategy...")

        result = await self.execute_cli_command(command, timeout=600)

        await self.update_progress(80, "Processing review...")

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

        await self.update_progress(100, "Strategy review complete")

        return {
            "success": True,
            "ticker": params.ticker,
            "output": result["stdout"],
        }

    async def execute_sector_compare(
        self,
        params: SectorCompareRequest,
    ) -> dict[str, Any]:
        """
        Execute sector comparison.

        Args:
            params: Sector compare parameters

        Returns:
            Command result dictionary
        """
        await self.update_progress(10, "Loading sector data...")

        command = params.to_cli_args()

        await self.update_progress(40, "Comparing sector performance...")

        result = await self.execute_cli_command(command, timeout=300)

        await self.update_progress(80, "Processing comparison results...")

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

        await self.update_progress(100, "Sector comparison complete")

        return {
            "success": True,
            "format": params.output_format,
            "output": result["stdout"],
        }

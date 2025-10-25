"""
Seasonality command service for executing seasonality analysis commands.
"""

from typing import Any

from ...models.schemas import (
    SeasonalityCleanRequest,
    SeasonalityCurrentRequest,
    SeasonalityListRequest,
    SeasonalityPortfolioRequest,
    SeasonalityResultsRequest,
    SeasonalityRunRequest,
)
from ..base import BaseCommandService


class SeasonalityService(BaseCommandService):
    """Service for executing seasonality commands."""

    async def execute_run(self, params: SeasonalityRunRequest) -> dict[str, Any]:
        """Execute seasonality run command."""
        await self.update_progress(10, "Initializing seasonality analysis...")

        command = params.to_cli_args()

        await self.update_progress(30, "Loading price data...")
        await self.update_progress(50, "Analyzing seasonal patterns...")
        await self.update_progress(70, "Calculating statistics...")

        result = await self.execute_cli_command(command, timeout=900)

        await self.update_progress(90, "Processing results...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Seasonality analysis complete")

        return {
            "success": True,
            "tickers": params.tickers,
            "output": result["stdout"],
        }

    async def execute_list(self, params: SeasonalityListRequest) -> dict[str, Any]:
        """Execute seasonality list command."""
        await self.update_progress(30, "Loading available tickers...")

        command = params.to_cli_args()

        await self.update_progress(70, "Retrieving ticker list...")

        result = await self.execute_cli_command(command, timeout=60)

        await self.update_progress(90, "Formatting results...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Ticker list retrieved")

        return {"success": True, "output": result["stdout"]}

    async def execute_results(
        self, params: SeasonalityResultsRequest
    ) -> dict[str, Any]:
        """Execute seasonality results command."""
        await self.update_progress(20, "Loading seasonality results...")

        command = params.to_cli_args()

        await self.update_progress(60, f"Retrieving results for {params.ticker}...")

        result = await self.execute_cli_command(command, timeout=60)

        await self.update_progress(90, "Formatting results...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Results retrieved")

        return {"success": True, "ticker": params.ticker, "output": result["stdout"]}

    async def execute_clean(self, params: SeasonalityCleanRequest) -> dict[str, Any]:
        """Execute seasonality clean command."""
        await self.update_progress(30, "Cleaning results directory...")

        command = params.to_cli_args()

        await self.update_progress(70, "Removing files...")

        result = await self.execute_cli_command(command, timeout=60)

        await self.update_progress(90, "Verifying cleanup...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Cleanup complete")

        return {"success": True, "output": result["stdout"]}

    async def execute_current(
        self, params: SeasonalityCurrentRequest
    ) -> dict[str, Any]:
        """Execute seasonality current command."""
        await self.update_progress(10, "Analyzing current seasonality patterns...")

        command = params.to_cli_args()

        await self.update_progress(30, "Loading historical data...")
        await self.update_progress(50, "Calculating expectancy...")
        await self.update_progress(70, "Identifying opportunities...")

        result = await self.execute_cli_command(command, timeout=900)

        await self.update_progress(90, "Processing results...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Current expectancy analysis complete")

        return {"success": True, "output": result["stdout"]}

    async def execute_portfolio(
        self, params: SeasonalityPortfolioRequest
    ) -> dict[str, Any]:
        """Execute seasonality portfolio command."""
        await self.update_progress(10, "Loading portfolio...")

        command = params.to_cli_args()

        await self.update_progress(25, "Analyzing portfolio tickers...")
        await self.update_progress(50, "Running seasonality analysis...")
        await self.update_progress(75, "Calculating patterns...")

        result = await self.execute_cli_command(command, timeout=1200)

        await self.update_progress(90, "Processing portfolio results...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Portfolio seasonality analysis complete")

        return {
            "success": True,
            "portfolio": params.portfolio_name,
            "output": result["stdout"],
        }

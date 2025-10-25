"""
Concurrency command service for executing concurrency analysis commands.
"""

from typing import Any

from ...models.schemas import (
    ConcurrencyAnalyzeRequest,
    ConcurrencyConstructRequest,
    ConcurrencyDemoRequest,
    ConcurrencyExportRequest,
    ConcurrencyHealthRequest,
    ConcurrencyMonteCarloRequest,
    ConcurrencyOptimizeRequest,
    ConcurrencyReviewRequest,
)
from ..base import BaseCommandService


class ConcurrencyService(BaseCommandService):
    """Service for executing concurrency commands."""

    async def execute_analyze(
        self, params: ConcurrencyAnalyzeRequest
    ) -> dict[str, Any]:
        """Execute concurrency analyze command."""
        await self.update_progress(5, "Initializing concurrency analysis...")

        command = params.to_cli_args()

        await self.update_progress(20, "Loading portfolio strategies...")
        await self.update_progress(40, "Analyzing concurrent exposure...")
        await self.update_progress(60, "Calculating risk concentration...")

        result = await self.execute_cli_command(command, timeout=1800)

        await self.update_progress(90, "Processing results...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Concurrency analysis complete")

        return {
            "success": True,
            "portfolio": params.portfolio,
            "output": result["stdout"],
        }

    async def execute_export(self, params: ConcurrencyExportRequest) -> dict[str, Any]:
        """Execute concurrency export command."""
        await self.update_progress(10, "Preparing export...")

        command = params.to_cli_args()

        await self.update_progress(50, "Exporting trade history...")

        result = await self.execute_cli_command(command, timeout=600)

        await self.update_progress(90, "Finalizing export...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Export complete")

        return {
            "success": True,
            "portfolio": params.portfolio,
            "output": result["stdout"],
        }

    async def execute_review(self, params: ConcurrencyReviewRequest) -> dict[str, Any]:
        """Execute concurrency review command."""
        await self.update_progress(10, "Loading portfolio for review...")

        command = params.to_cli_args()

        await self.update_progress(50, f"Analyzing {params.focus}...")

        result = await self.execute_cli_command(command, timeout=600)

        await self.update_progress(90, "Processing review...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Portfolio review complete")

        return {
            "success": True,
            "portfolio": params.portfolio,
            "output": result["stdout"],
        }

    async def execute_construct(
        self, params: ConcurrencyConstructRequest
    ) -> dict[str, Any]:
        """Execute concurrency construct command."""
        await self.update_progress(10, "Discovering strategies...")

        command = params.to_cli_args()

        await self.update_progress(30, "Evaluating strategy combinations...")
        await self.update_progress(60, "Optimizing portfolio...")

        result = await self.execute_cli_command(command, timeout=900)

        await self.update_progress(90, "Finalizing portfolio construction...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Portfolio construction complete")

        return {"success": True, "output": result["stdout"]}

    async def execute_optimize(
        self, params: ConcurrencyOptimizeRequest
    ) -> dict[str, Any]:
        """Execute concurrency optimize command."""
        await self.update_progress(5, "Initializing optimization...")

        command = params.to_cli_args()

        await self.update_progress(15, "Loading portfolio strategies...")
        await self.update_progress(30, "Testing permutations...")
        await self.update_progress(60, "Evaluating combinations...")

        result = await self.execute_cli_command(command, timeout=3600)

        await self.update_progress(90, "Processing optimization results...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Portfolio optimization complete")

        return {
            "success": True,
            "portfolio": params.portfolio,
            "output": result["stdout"],
        }

    async def execute_monte_carlo(
        self, params: ConcurrencyMonteCarloRequest
    ) -> dict[str, Any]:
        """Execute Monte Carlo simulation."""
        await self.update_progress(5, "Initializing Monte Carlo simulation...")

        command = params.to_cli_args()

        await self.update_progress(15, "Loading portfolio data...")
        await self.update_progress(30, "Running simulations...")
        await self.update_progress(70, "Calculating statistics...")

        result = await self.execute_cli_command(command, timeout=2400)

        await self.update_progress(90, "Processing simulation results...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Monte Carlo simulation complete")

        return {
            "success": True,
            "portfolio": params.portfolio,
            "output": result["stdout"],
        }

    async def execute_health(self, params: ConcurrencyHealthRequest) -> dict[str, Any]:
        """Execute concurrency health check."""
        await self.update_progress(20, "Running health checks...")

        command = params.to_cli_args()

        await self.update_progress(60, "Checking system components...")

        result = await self.execute_cli_command(command, timeout=120)

        await self.update_progress(90, "Processing health results...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Health check complete")

        return {"success": True, "output": result["stdout"]}

    async def execute_demo(self, params: ConcurrencyDemoRequest) -> dict[str, Any]:
        """Execute concurrency demo."""
        await self.update_progress(10, "Creating demo portfolio...")

        command = params.to_cli_args()

        await self.update_progress(40, "Generating sample data...")
        await self.update_progress(70, "Running demo analysis...")

        result = await self.execute_cli_command(command, timeout=600)

        await self.update_progress(90, "Processing demo results...")

        if not result["success"]:
            error_msg = result.get("stderr") or result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "CLI_EXECUTION_ERROR")
            await self.update_progress(0, f"Failed: {error_msg}")
            # Raise exception so task handler marks job as FAILED
            raise RuntimeError(f"{error_type}: {error_msg}")

        await self.update_progress(100, "Demo complete")

        return {"success": True, "output": result["stdout"]}

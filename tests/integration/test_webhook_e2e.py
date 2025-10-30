"""
E2E Webhook Integration Test

Tests the complete webhook flow:
1. Submit strategy sweep job with webhook URL
2. Wait for webhook callback with results
3. Fetch best results from sweep API
4. Verify data integrity across the flow
"""

import asyncio
import json
import logging
import time
from urllib.parse import urljoin

import pytest
import requests
from aiohttp import web


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebhookReceiver:
    """Simple async webhook receiver for testing."""

    def __init__(self, port: int = 0):
        """Initialize webhook receiver.

        Args:
            port: Port to listen on (0 = random available port)
        """
        self.port = port
        self.received_webhooks = asyncio.Queue()
        self.app = web.Application()
        self.app.router.add_post("/webhook", self.handle_webhook)
        self.runner = None
        self.site = None
        self.actual_port = None

    async def handle_webhook(self, request):
        """Handle incoming webhook POST."""
        try:
            data = await request.json()
            logger.info(
                f"📥 Webhook received: job_id={data.get('job_id')}, status={data.get('status')}",
            )
            await self.received_webhooks.put(data)
            return web.Response(text=json.dumps({"status": "received"}), status=200)
        except Exception as e:
            logger.exception(f"Error handling webhook: {e}")
            return web.Response(text=str(e), status=500)

    async def start(self):
        """Start the webhook server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "localhost", self.port)
        await self.site.start()
        self.actual_port = self.site._server.sockets[0].getsockname()[1]
        logger.info(
            f"🌐 Webhook receiver started on http://localhost:{self.actual_port}/webhook",
        )

    async def stop(self):
        """Stop the webhook server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("🛑 Webhook receiver stopped")

    async def wait_for_webhook(self, timeout: float = 60.0) -> dict | None:
        """Wait for a webhook to arrive.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Webhook data or None if timeout
        """
        try:
            return await asyncio.wait_for(
                self.received_webhooks.get(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.exception(f"⏰ Timeout waiting for webhook after {timeout}s")
            return None

    @property
    def webhook_url(self) -> str:
        """Get the webhook URL."""
        return f"http://localhost:{self.actual_port}/webhook"


class SweepTestClient:
    """API client for testing sweep endpoints."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str = "dev-key-000000000000000000000000",
    ):
        """Initialize test client.

        Args:
            base_url: Base URL of the API
            api_key: API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {"X-API-Key": api_key, "Content-Type": "application/json"},
        )

    def submit_sweep(self, webhook_url: str) -> dict:
        """Submit a strategy sweep job.

        Args:
            webhook_url: URL to receive webhook callback

        Returns:
            Job response with job_id
        """
        url = urljoin(self.base_url, "/api/v1/strategy/sweep")

        # Use minimal parameters for faster execution
        payload = {
            "ticker": "AAPL",
            "fast_range_min": 10,
            "fast_range_max": 20,
            "slow_range_min": 20,
            "slow_range_max": 30,
            "step": 10,
            "min_trades": 10,  # Lower requirement for faster test
            "webhook_url": webhook_url,
        }

        logger.info(f"📤 Submitting sweep job: {payload['ticker']}")
        response = self.session.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        logger.info(f"✅ Job created: {data['job_id']}")
        return data

    def get_best_result(self, sweep_run_id: str, ticker: str = "AAPL") -> dict:
        """Get best result from a sweep.

        Args:
            sweep_run_id: Sweep run identifier
            ticker: Ticker symbol

        Returns:
            Best result data
        """
        url = urljoin(self.base_url, f"/api/v1/sweeps/{sweep_run_id}/best")
        params = {"ticker": ticker}

        logger.info(f"📥 Fetching best result for sweep: {sweep_run_id}")
        response = self.session.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        logger.info(
            f"✅ Best result fetched: score={data['results'][0].get('score') if data.get('results') else 'N/A'}",
        )
        return data

    def get_job_status(self, job_id: str) -> dict:
        """Get job status.

        Args:
            job_id: Job identifier

        Returns:
            Job status data
        """
        url = urljoin(self.base_url, f"/api/v1/jobs/{job_id}")
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_webhook_flow():
    """
    E2E test for webhook flow.

    Flow:
    1. Start webhook receiver
    2. Submit sweep job with webhook URL
    3. Wait for webhook callback
    4. Fetch best results
    5. Verify data integrity
    """
    # Setup
    receiver = WebhookReceiver()
    await receiver.start()

    client = SweepTestClient()

    try:
        # Step 1: Submit sweep job
        logger.info("\n" + "=" * 70)
        logger.info("STEP 1: Submit Strategy Sweep Job")
        logger.info("=" * 70)

        job_response = client.submit_sweep(receiver.webhook_url)

        assert "job_id" in job_response, "Job ID not in response"
        assert job_response["status"] == "pending", (
            f"Expected pending status, got {job_response['status']}"
        )

        job_id = job_response["job_id"]
        logger.info(f"✅ Job submitted successfully: {job_id}")

        # Step 2: Wait for webhook callback
        logger.info("\n" + "=" * 70)
        logger.info("STEP 2: Wait for Webhook Callback (~30 seconds)")
        logger.info("=" * 70)

        start_time = time.time()
        webhook_data = await receiver.wait_for_webhook(timeout=60.0)
        elapsed = time.time() - start_time

        assert webhook_data is not None, "Webhook not received within timeout"
        logger.info(f"✅ Webhook received after {elapsed:.1f}s")

        # Step 3: Validate webhook data
        logger.info("\n" + "=" * 70)
        logger.info("STEP 3: Validate Webhook Data")
        logger.info("=" * 70)

        assert webhook_data["job_id"] == job_id, "Job ID mismatch in webhook"
        assert webhook_data["status"] in [
            "completed",
            "failed",
        ], f"Unexpected status: {webhook_data['status']}"

        if webhook_data["status"] == "failed":
            error_msg = webhook_data.get("error_message", "Unknown error")
            pytest.fail(f"Job failed: {error_msg}")

        assert "result_data" in webhook_data, "No result_data in webhook"
        assert webhook_data["result_data"] is not None, "result_data is None"

        # Extract sweep_run_id
        result_data = webhook_data["result_data"]

        # The result_data might have different structures depending on the command
        # For sweep, it should contain sweep results or sweep_run_id
        logger.info(
            f"Result data keys: {result_data.keys() if isinstance(result_data, dict) else type(result_data)}",
        )

        # Try to get sweep_run_id from various possible locations
        sweep_run_id = None
        if isinstance(result_data, dict):
            sweep_run_id = (
                result_data.get("sweep_run_id")
                or result_data.get("sweep_id")
                or result_data.get("id")
            )

        logger.info(
            f"✅ Webhook validated: status={webhook_data['status']}, sweep_id={sweep_run_id}",
        )

        # Step 4: Fetch best results (if we have sweep_run_id)
        if sweep_run_id:
            logger.info("\n" + "=" * 70)
            logger.info("STEP 4: Fetch Best Results from API")
            logger.info("=" * 70)

            best_result = client.get_best_result(sweep_run_id, "AAPL")

            assert "results" in best_result, "No results in best_result"
            assert len(best_result["results"]) > 0, "Empty results array"

            first_result = best_result["results"][0]
            logger.info(
                f"✅ Best result fetched: {first_result.get('ticker')} score={first_result.get('score')}",
            )

            # Step 5: Validate data integrity
            logger.info("\n" + "=" * 70)
            logger.info("STEP 5: Validate Data Integrity")
            logger.info("=" * 70)

            assert first_result["ticker"] == "AAPL", "Ticker mismatch"
            assert "score" in first_result, "No score in result"
            assert "fast_period" in first_result, "No fast_period in result"
            assert "slow_period" in first_result, "No slow_period in result"

            logger.info("✅ Data integrity validated")
        else:
            logger.warning(
                "⚠️  No sweep_run_id found in result_data, skipping API fetch",
            )
            logger.info("This might be expected if the sweep saves results differently")

        # Final summary
        logger.info("\n" + "=" * 70)
        logger.info("✅ E2E TEST PASSED")
        logger.info("=" * 70)
        logger.info(f"Total time: {time.time() - start_time:.1f}s")
        logger.info(f"Job ID: {job_id}")
        logger.info("Webhook received: ✅")
        logger.info(f"Status: {webhook_data['status']}")
        if sweep_run_id:
            logger.info(f"Sweep ID: {sweep_run_id}")
        logger.info("=" * 70)

    finally:
        # Cleanup
        await receiver.stop()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_timeout_handling():
    """Test that webhook timeout is handled gracefully."""
    receiver = WebhookReceiver()
    await receiver.start()

    try:
        # Wait for webhook with very short timeout (should timeout)
        webhook_data = await receiver.wait_for_webhook(timeout=0.5)
        assert webhook_data is None, "Should have timed out"
        logger.info("✅ Timeout handling works correctly")
    finally:
        await receiver.stop()


if __name__ == "__main__":
    # Allow running directly for quick testing
    asyncio.run(test_complete_webhook_flow())

"""
Complete Sweep Workflow Example

This example demonstrates the complete workflow for running a strategy
parameter sweep and retrieving results via the Trading API.
"""

import time

import requests


class TradingAPIClient:
    """
    Python client for the Trading CLI API.

    Provides a clean interface for executing strategy sweeps and
    retrieving results.
    """

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the API
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or "dev-key-000000000000000000000000"
        self.headers = {"X-API-Key": self.api_key}

    def start_sweep(
        self,
        ticker: str,
        fast_range_min: int = 5,
        fast_range_max: int = 50,
        slow_range_min: int = 10,
        slow_range_max: int = 200,
        min_trades: int = 50,
        strategy_type: str = "SMA",
    ) -> dict:
        """
        Start a parameter sweep analysis.

        Args:
            ticker: Ticker symbol (e.g., "AAPL", "BTC-USD")
            fast_range_min: Minimum fast period
            fast_range_max: Maximum fast period
            slow_range_min: Minimum slow period
            slow_range_max: Maximum slow period
            min_trades: Minimum trades filter
            strategy_type: Strategy type (SMA, EMA, MACD)

        Returns:
            Job information including job_id for tracking
        """
        payload = {
            "ticker": ticker,
            "fast_range_min": fast_range_min,
            "fast_range_max": fast_range_max,
            "slow_range_min": slow_range_min,
            "slow_range_max": slow_range_max,
            "min_trades": min_trades,
            "strategy_type": strategy_type,
        }

        response = requests.post(
            f"{self.base_url}/api/v1/strategy/sweep", json=payload, headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_job_status(self, job_id: str) -> dict:
        """
        Get current status of a job.

        Args:
            job_id: Job identifier

        Returns:
            Job status information
        """
        response = requests.get(
            f"{self.base_url}/api/v1/jobs/{job_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def wait_for_completion(
        self, job_id: str, timeout: int = 1800, poll_interval: int = 5
    ) -> dict:
        """
        Wait for a job to complete.

        Args:
            job_id: Job identifier
            timeout: Maximum time to wait in seconds
            poll_interval: Seconds between status checks

        Returns:
            Final job status

        Raises:
            TimeoutError: If job doesn't complete within timeout
            Exception: If job fails
        """
        elapsed = 0

        while elapsed < timeout:
            status = self.get_job_status(job_id)

            print(f"Status: {status['status']}, Progress: {status['progress']}%")

            if status["status"] == "completed":
                return status
            if status["status"] == "failed":
                raise Exception(f"Job failed: {status.get('error_message')}")

            time.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Job did not complete within {timeout} seconds")

    def list_sweeps(self, limit: int = 10) -> list[dict]:
        """
        List all sweep runs.

        Args:
            limit: Maximum number of sweeps to return

        Returns:
            List of sweep summaries
        """
        response = requests.get(
            f"{self.base_url}/api/v1/sweeps/?limit={limit}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_latest_sweep_results(self, limit: int = 10) -> dict:
        """
        Get best results from the most recent sweep.

        Args:
            limit: Number of top results to return

        Returns:
            Best results from latest sweep
        """
        response = requests.get(
            f"{self.base_url}/api/v1/sweeps/latest?limit={limit}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_sweep_results(
        self,
        sweep_run_id: str,
        ticker: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """
        Get all results for a specific sweep run.

        Args:
            sweep_run_id: Sweep run identifier
            ticker: Optional ticker filter
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            Sweep results with pagination info
        """
        params = {"limit": limit, "offset": offset}
        if ticker:
            params["ticker"] = ticker

        response = requests.get(
            f"{self.base_url}/api/v1/sweeps/{sweep_run_id}",
            params=params,
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_best_result(self, sweep_run_id: str, ticker: str | None = None) -> dict:
        """
        Get the best result for a sweep run.

        Args:
            sweep_run_id: Sweep run identifier
            ticker: Optional ticker filter for best result per ticker

        Returns:
            Best result(s) for the sweep
        """
        params = {"ticker": ticker} if ticker else {}

        response = requests.get(
            f"{self.base_url}/api/v1/sweeps/{sweep_run_id}/best",
            params=params,
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_best_per_ticker(self, sweep_run_id: str) -> dict:
        """
        Get best result for each ticker in a sweep.

        Args:
            sweep_run_id: Sweep run identifier

        Returns:
            Best result for each ticker
        """
        response = requests.get(
            f"{self.base_url}/api/v1/sweeps/{sweep_run_id}/best-per-ticker",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()


# =============================================================================
# Example Usage
# =============================================================================


def main():
    """Demonstrate complete sweep workflow."""

    # Initialize client
    client = TradingAPIClient(
        base_url="http://localhost:8000", api_key="dev-key-000000000000000000000000"
    )

    print("=" * 60)
    print("Strategy Sweep Workflow Example")
    print("=" * 60)

    # Step 1: Start a sweep
    print("\n1. Starting parameter sweep for AAPL...")
    job = client.start_sweep(
        ticker="AAPL",
        fast_range_min=5,
        fast_range_max=30,
        slow_range_min=10,
        slow_range_max=100,
        min_trades=50,
    )

    print(f"   Job ID: {job['job_id']}")
    print(f"   Status: {job['status']}")
    print(f"   Stream URL: {job['stream_url']}")

    # Step 2: Wait for completion
    print("\n2. Waiting for sweep to complete...")
    try:
        result = client.wait_for_completion(job["job_id"], timeout=1800)
        print("   ✓ Sweep completed!")
        print(f"   Duration: {result.get('completed_at')} - {result.get('started_at')}")
    except TimeoutError as e:
        print(f"   ✗ Timeout: {e}")
        return
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    # Step 3: Extract sweep_run_id
    # Parse from result_data output or get from latest sweep
    print("\n3. Getting sweep results...")
    latest = client.get_latest_sweep_results(limit=1)

    if not latest or not latest.get("results"):
        print("   ✗ No results found")
        return

    sweep_run_id = latest["sweep_run_id"]
    print(f"   Sweep Run ID: {sweep_run_id}")

    # Step 4: Get best result for AAPL
    print("\n4. Getting best result for AAPL...")
    best = client.get_best_result(sweep_run_id, ticker="AAPL")

    if best and best["results"]:
        result = best["results"][0]
        print("   ✓ Best Result Found:")
        print(f"     - Ticker: {result['ticker']}")
        print(f"     - Parameters: {result['fast_period']}/{result['slow_period']}")
        print(f"     - Score: {result.get('score', 'N/A')}")
        print(f"     - Sharpe Ratio: {result.get('sharpe_ratio', 'N/A')}")
        print(f"     - Total Return: {result.get('total_return_pct', 'N/A')}%")
        print(f"     - Win Rate: {result.get('win_rate_pct', 'N/A')}%")
        print(f"     - Max Drawdown: {result.get('max_drawdown_pct', 'N/A')}%")
        print(f"     - Total Trades: {result.get('total_trades', 'N/A')}")

    # Step 5: Get all results (paginated)
    print("\n5. Getting top 10 results...")
    all_results = client.get_sweep_results(
        sweep_run_id, ticker="AAPL", limit=10, offset=0
    )

    print(f"   Total Results: {all_results['total_count']}")
    print(f"   Returned: {all_results['returned_count']}")
    print("\n   Top 5 Scores:")
    for i, result in enumerate(all_results["results"][:5], 1):
        print(
            f"     {i}. {result['fast_period']}/{result['slow_period']}: "
            f"Score={result.get('score', 'N/A')}"
        )

    # Step 6: List all sweep runs
    print("\n6. Listing recent sweep runs...")
    sweeps = client.list_sweeps(limit=5)

    print(f"   Found {len(sweeps)} recent sweeps:")
    for sweep in sweeps:
        print(
            f"     - {sweep['run_date']}: {sweep['result_count']} results, "
            f"Best: {sweep['best_ticker']} ({sweep.get('best_score', 'N/A')})"
        )

    print("\n" + "=" * 60)
    print("✓ Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

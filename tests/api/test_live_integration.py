"""
Live integration tests for Trading CLI API.

These tests hit the actual running API on http://localhost:8000
Run this while the API is running with: ./scripts/start_api.sh

Prerequisites:
- API running on http://localhost:8000
- Database tables created
- ARQ worker running
"""

import requests


# Test API key
TEST_API_KEY = "dev-key-000000000000000000000000"
BASE_URL = "http://localhost:8000"


class TestLiveAPI:
    """Test the live API."""

    def test_api_is_running(self):
        """Verify API is accessible."""
        response = requests.get(f"{BASE_URL}/health/")
        assert (
            response.status_code == 200
        ), "API is not running on http://localhost:8000"
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        print(f"✓ API is running: {data['status']}")

    def test_health_components(self):
        """Test detailed health check."""
        response = requests.get(f"{BASE_URL}/health/detailed")
        assert response.status_code == 200
        data = response.json()

        assert "components" in data
        assert "database" in data["components"]
        assert "redis" in data["components"]

        print(f"✓ Database: {data['components']['database']['status']}")
        print(f"✓ Redis: {data['components']['redis']['status']}")


class TestStrategyEndpoints:
    """Test strategy command endpoints."""

    def test_strategy_run_creates_job(self):
        """Test strategy run endpoint creates a job."""
        response = requests.post(
            f"{BASE_URL}/api/v1/strategy/run",
            json={
                "ticker": "BTC-USD",
                "fast_period": 10,
                "slow_period": 20,
                "config_path": "app/cli/profiles/strategies/minimum.yaml",
            },
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert response.status_code in [
            200,
            201,
            202,
        ], f"Got {response.status_code}: {response.text}"
        data = response.json()

        # Verify response structure
        assert "job_id" in data, f"Missing job_id in response: {data}"
        assert "status" in data
        assert "status_url" in data
        assert "stream_url" in data

        # Verify status
        assert data["status"] in ["pending", "running", "completed"]

        print(f"✓ Strategy run job created: {data['job_id']}")
        print(f"  Status: {data['status']}")
        print(f"  Status URL: {data['status_url']}")

        return data["job_id"]

    def test_strategy_sweep_creates_job(self):
        """Test strategy sweep endpoint with form-encoded data."""
        response = requests.post(
            f"{BASE_URL}/api/v1/strategy/sweep",
            json={  # Send as JSON
                "ticker": "BTC-USD",
                "fast_range_min": 5,
                "fast_range_max": 15,
                "slow_range_min": 20,
                "slow_range_max": 40,
                "step": 5,
                "config_path": "app/cli/profiles/strategies/minimum.yaml",
            },
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert response.status_code in [
            200,
            201,
            202,
        ], f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "job_id" in data
        print(f"✓ Strategy sweep job created: {data['job_id']}")

    def test_strategy_review_validation(self):
        """Test strategy review requires ticker."""
        response = requests.post(
            f"{BASE_URL}/api/v1/strategy/review",
            json={
                "config_path": "app/cli/profiles/strategies/minimum.yaml",
            },
            headers={"X-API-Key": TEST_API_KEY},
        )

        # Should fail validation - ticker is required
        assert response.status_code == 422
        print("✓ Strategy review validation working")

    def test_job_status_retrieval(self):
        """Test retrieving job status."""
        # First create a job
        create_response = requests.post(
            f"{BASE_URL}/api/v1/strategy/run",
            json={
                "ticker": "TSLA",
                "fast_period": 12,
                "slow_period": 26,
                "config_path": "app/cli/profiles/strategies/minimum.yaml",
            },
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert create_response.status_code in [200, 201, 202]
        job_id = create_response.json()["job_id"]

        # Retrieve status
        status_response = requests.get(
            f"{BASE_URL}/api/v1/jobs/{job_id}",
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert status_response.status_code == 200
        status_data = status_response.json()

        assert status_data["job_id"] == job_id
        assert status_data["command_group"] == "strategy"
        assert status_data["command_name"] == "run"
        assert status_data["status"] in ["pending", "running", "completed", "failed"]

        print(f"✓ Job status retrieved: {job_id}")
        print(f"  Status: {status_data['status']}")


class TestConfigEndpoints:
    """Test config command endpoints."""

    def test_config_list(self):
        """Test config list endpoint."""
        response = requests.post(
            f"{BASE_URL}/api/v1/config/list",
            json={"detailed": False},
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert response.status_code in [200, 201, 202]
        data = response.json()
        assert "job_id" in data
        print(f"✓ Config list job created: {data['job_id']}")

    def test_config_show(self):
        """Test config show endpoint."""
        response = requests.post(
            f"{BASE_URL}/api/v1/config/show",
            json={"profile_name": "minimum"},
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert response.status_code in [200, 201, 202]
        data = response.json()
        assert "job_id" in data
        print(f"✓ Config show job created: {data['job_id']}")


class TestConcurrencyEndpoints:
    """Test concurrency command endpoints."""

    def test_concurrency_analyze(self):
        """Test concurrency analyze endpoint."""
        response = requests.post(
            f"{BASE_URL}/api/v1/concurrency/analyze",
            json={
                "portfolio": "data/raw/strategies/portfolio.csv",
                "method": "pearson",
            },
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert response.status_code in [
            200,
            201,
            202,
        ], f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "job_id" in data
        print(f"✓ Concurrency analyze job created: {data['job_id']}")

    def test_concurrency_health(self):
        """Test concurrency health endpoint."""
        response = requests.post(
            f"{BASE_URL}/api/v1/concurrency/health",
            json={},
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert response.status_code in [200, 201, 202]
        data = response.json()
        assert "job_id" in data
        print(f"✓ Concurrency health job created: {data['job_id']}")


class TestSeasonalityEndpoints:
    """Test seasonality command endpoints."""

    def test_seasonality_list(self):
        """Test seasonality list endpoint."""
        response = requests.post(
            f"{BASE_URL}/api/v1/seasonality/list",
            json={},
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert response.status_code in [200, 201, 202]
        data = response.json()
        assert "job_id" in data
        print(f"✓ Seasonality list job created: {data['job_id']}")

    def test_seasonality_run(self):
        """Test seasonality run endpoint."""
        response = requests.post(
            f"{BASE_URL}/api/v1/seasonality/run",
            json={
                "ticker": "BTC-USD",
                "analysis_type": "monthly",
            },
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert response.status_code in [200, 201, 202]
        data = response.json()
        assert "job_id" in data
        print(f"✓ Seasonality run job created: {data['job_id']}")


class TestJobManagement:
    """Test job management endpoints."""

    def test_job_list(self):
        """Test listing jobs."""
        response = requests.get(
            f"{BASE_URL}/api/v1/jobs/",
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert response.status_code == 200
        data = response.json()

        # Response is a list of jobs
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify job structure
        if len(data) > 0:
            job = data[0]
            assert "job_id" in job
            assert "status" in job
            assert "command_group" in job
            assert "command_name" in job

        print(f"✓ Job list retrieved: {len(data)} jobs")

    def test_complete_job_lifecycle(self):
        """Test complete job lifecycle: create → status → list."""
        # Step 1: Create a job
        create_response = requests.post(
            f"{BASE_URL}/api/v1/strategy/run",
            json={
                "ticker": "AAPL",
                "fast_period": 15,
                "slow_period": 30,
                "config_path": "app/cli/profiles/strategies/minimum.yaml",
            },
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert create_response.status_code in [200, 201, 202]
        job_data = create_response.json()
        job_id = job_data["job_id"]

        print(f"\n✓ Job created: {job_id}")
        print(f"  Initial status: {job_data['status']}")

        # Step 2: Check status
        status_response = requests.get(
            f"{BASE_URL}/api/v1/jobs/{job_id}",
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert status_response.status_code == 200
        status_data = status_response.json()

        print(f"✓ Status retrieved: {status_data['status']}")
        print(
            f"  Command: {status_data['command_group']}.{status_data['command_name']}",
        )

        # Step 3: Verify in list
        list_response = requests.get(
            f"{BASE_URL}/api/v1/jobs/",
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert list_response.status_code == 200
        list_data = list_response.json()

        # list_data is a list of jobs
        job_ids = [job["job_id"] for job in list_data]
        assert job_id in job_ids

        print(f"✓ Job found in list (total: {len(list_data)})")
        print("✓ Complete lifecycle test passed!")


class TestAuthentication:
    """Test authentication and authorization."""

    def test_no_api_key_fails(self):
        """Test request without API key fails."""
        response = requests.post(
            f"{BASE_URL}/api/v1/config/list",
            json={},
        )
        assert response.status_code == 401
        print("✓ No API key → 401")

    def test_invalid_api_key_fails(self):
        """Test request with invalid API key fails."""
        response = requests.post(
            f"{BASE_URL}/api/v1/config/list",
            json={},
            headers={"X-API-Key": "invalid-key-123"},
        )
        assert response.status_code == 401
        print("✓ Invalid API key → 401")

    def test_valid_api_key_works(self):
        """Test request with valid API key works."""
        response = requests.post(
            f"{BASE_URL}/api/v1/config/list",
            json={},
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert response.status_code in [200, 201, 202]
        print("✓ Valid API key → Success")


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v", "-s"])

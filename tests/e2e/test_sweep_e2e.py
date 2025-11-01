import asyncio
import os

import httpx
import pytest

from .helpers import stream_sse, wait_for_api


API_BASE = os.getenv("E2E_API", "http://localhost:8000")
API_KEY = os.getenv("E2E_API_KEY", "dev-key-000000000000000000000000")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_sweep_e2e() -> None:
    async with httpx.AsyncClient(timeout=60) as client:
        # Wait for API to be healthy
        await wait_for_api(client, f"{API_BASE}/health/", 180)

        # 1) Submit sweep job
        sweep_params = {
            "ticker": "NVDA",
            "fast_range": [10, 20],
            "slow_range": [20, 30],
            "step": 5,
            "strategy_type": "SMA",
            "min_trades": 50,
        }

        resp = await client.post(
            f"{API_BASE}/api/v1/strategy/sweep",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json=sweep_params,
        )
        resp.raise_for_status()
        job_id = resp.json()["job_id"]

        # 2) Authenticate to get session cookie (for SSE proxy)
        auth = await client.post(
            f"{API_BASE}/api/v1/auth/login",
            headers={"Content-Type": "application/json"},
            json={"api_key": API_KEY},
        )
        auth.raise_for_status()
        set_cookie = auth.headers.get("set-cookie")
        assert set_cookie, "No session cookie received"
        session_cookie = set_cookie.split(";", 1)[0]

        # 3) Stream SSE for progress and completion
        sse_url = f"{API_BASE}/sse-proxy/jobs/{job_id}/stream"
        headers = {"Cookie": session_cookie}

        sweep_run_id = None
        # Provide a generous max duration (30m)
        deadline = asyncio.get_event_loop().time() + 30 * 60
        async for event in stream_sse(sse_url, headers=headers, connect_timeout=10):
            now = asyncio.get_event_loop().time()
            if now > deadline:
                pytest.fail("SSE timeout waiting for job completion")

            data = event.get("data_json")
            if not data:
                continue

            if data.get("error"):
                pytest.fail(f"Job failed: {data}")

            if data.get("done"):
                sweep_run_id = (
                    data.get("result_data", {}).get("sweep_run_id")
                    if isinstance(data.get("result_data"), dict)
                    else None
                )
                break

        # 4) Fallback: if SSE didn't provide sweep_run_id, fetch final job status
        if not sweep_run_id:
            print("⚠️  sweep_run_id not found in SSE stream, querying job status API...")
            status_resp = await client.get(
                f"{API_BASE}/api/v1/jobs/{job_id}", headers={"X-API-Key": API_KEY}
            )
            status_resp.raise_for_status()
            job_data = status_resp.json()
            result_data = job_data.get("result_data") or {}
            sweep_run_id = result_data.get("sweep_run_id")

            # Debug logging
            print(f"📊 Job Status: {job_data.get('status')}")
            print(f"📊 Job Progress: {job_data.get('progress')}")
            print(
                f"📊 Result Data Keys: {list(result_data.keys()) if isinstance(result_data, dict) else type(result_data)}"
            )

            # Accept the case where the job is skipped because results are up-to-date
            if not sweep_run_id:
                output_text = result_data.get("output", "")
                print(
                    f"📋 CLI Output Preview (first 1000 chars):\n{output_text[:1000]}"
                )

                if (
                    "All analysis is complete and up-to-date!" in output_text
                    or "Skipping execution" in output_text
                ):
                    print("ℹ️  Job skipped (results already up-to-date)")
                    return

                # Enhanced error message
                error_msg = job_data.get("error_message", "No error message")
                pytest.fail(
                    f"No sweep_run_id found in completion data.\n"
                    f"Job Status: {job_data.get('status')}\n"
                    f"Error Message: {error_msg}\n"
                    f"Output Preview: {output_text[:500]}"
                )
        else:
            print(f"✅ sweep_run_id extracted from SSE: {sweep_run_id}")

        # 5) Retrieve results for the sweep
        results = await client.get(
            f"{API_BASE}/api/v1/sweeps/{sweep_run_id}?ticker={sweep_params['ticker']}",
            headers={"X-API-Key": API_KEY},
        )
        results.raise_for_status()

        # 6) Retrieve best result
        best = await client.get(
            f"{API_BASE}/api/v1/sweeps/{sweep_run_id}/best?ticker={sweep_params['ticker']}",
            headers={"X-API-Key": API_KEY},
        )
        best.raise_for_status()
        assert best.json(), "best result empty"

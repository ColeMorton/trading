#!/usr/bin/env python3
"""Wait for API health check to pass."""

import argparse
import sys
import time

import httpx


def wait_for_health(url: str, timeout: int = 60, interval: int = 1) -> int:
    """Wait for API health endpoint to respond successfully.

    Args:
        url: The health check URL to poll
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds

    Returns:
        0 if healthy, 1 if timeout or error
    """
    start = time.time()
    attempts = 0

    while time.time() - start < timeout:
        attempts += 1
        try:
            response = httpx.get(url, timeout=2)
            response.raise_for_status()
            elapsed = time.time() - start
            print(f"✓ API is ready after {attempts} attempts ({elapsed:.1f}s)")
            return 0
        except Exception as e:
            elapsed = time.time() - start
            if elapsed >= timeout:
                print(
                    f"✗ API did not become healthy in time after {attempts} attempts: {e}"
                )
                return 1
            time.sleep(interval)

    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wait for API health check")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/health/",
        help="Health check URL",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=1,
        help="Check interval in seconds",
    )

    args = parser.parse_args()
    sys.exit(wait_for_health(args.url, args.timeout, args.interval))

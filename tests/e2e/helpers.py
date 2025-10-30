import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import httpx


async def wait_for_api(
    client: httpx.AsyncClient, url: str, timeout_seconds: int
) -> None:
    """Wait until a GET to url succeeds or timeout elapses."""
    for _ in range(timeout_seconds):
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            return
        except Exception:
            await asyncio.sleep(1)
    raise TimeoutError("API not ready in allotted time")


async def stream_sse(
    url: str,
    headers: dict[str, str] | None = None,
    connect_timeout: float | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """Minimal SSE client yielding parsed events.

    Yields dicts with keys: data_raw (str), data_json (dict|None)
    """
    timeouts = httpx.Timeout(None, connect=connect_timeout)
    async with httpx.AsyncClient(timeout=timeouts) as client:
        async with client.stream("GET", url, headers=headers or {}) as resp:
            resp.raise_for_status()
            buffer = ""
            async for chunk in resp.aiter_text():
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data = line[6:]
                        yield {"data_raw": data, "data_json": _safe_json(data)}


def _safe_json(s: str) -> dict[str, Any] | None:
    try:
        import json

        return json.loads(s)
    except Exception:
        return None

"""
Trading CLI FastAPI Application.

FastAPI wrapper for the trading-cli application providing:
- Async job execution with ARQ
- Real-time progress streaming via SSE
- API key authentication
- Comprehensive job management

Version: 1.0.0-beta
"""

from .core.config import settings
from .main import app


__version__ = "1.0.0-beta"
__all__ = ["app", "settings"]

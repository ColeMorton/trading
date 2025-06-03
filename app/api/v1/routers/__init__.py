"""
API Version 1 Routers

This module contains all routers for API version 1.
"""

from .data import router as data_router
from .health import router as health_router
from .ma_cross import router as ma_cross_router
from .scripts import router as scripts_router

__all__ = ["scripts_router", "data_router", "ma_cross_router", "health_router"]

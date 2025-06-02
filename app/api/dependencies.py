"""
API Dependencies and Common Functions
"""

import os
from typing import Optional

def get_current_version() -> str:
    """Get the current application version"""
    return os.getenv("VERSION", "1.0.0")
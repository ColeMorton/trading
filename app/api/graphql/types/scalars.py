"""
GraphQL Scalar Types

This module defines custom scalar types for the GraphQL schema.
"""

import json
from datetime import datetime
from decimal import Decimal as PyDecimal
from typing import Any, Dict, List, Union

import strawberry


@strawberry.scalar(
    serialize=lambda v: v.isoformat() if v else None,
    parse_value=lambda v: datetime.fromisoformat(v) if isinstance(v, str) else v,
)
class DateTime:
    """DateTime scalar type that serializes to ISO format."""

    pass


@strawberry.scalar(
    serialize=lambda v: float(v) if v is not None else None,
    parse_value=lambda v: PyDecimal(str(v)) if v is not None else None,
)
class Decimal:
    """Decimal scalar type for precise numeric values."""

    pass


@strawberry.scalar(
    serialize=lambda v: (
        v if isinstance(v, (dict, list)) else json.dumps(v) if v is not None else None
    ),
    parse_value=lambda v: (
        v if isinstance(v, (dict, list)) else json.loads(v) if isinstance(v, str) else v
    ),
)
class JSON:
    """JSON scalar type for storing arbitrary JSON data."""

    pass

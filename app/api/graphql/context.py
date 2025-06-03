"""
GraphQL Context

This module provides context for GraphQL operations including database connections,
authentication, and request information.
"""

from typing import Any, Dict

from fastapi import Depends, Request

from app.api.utils.logging import setup_api_logging
from app.database.config import get_prisma

# Set up logging
log, _, logger, _ = setup_api_logging()


async def get_graphql_context(
    request: Request, database=Depends(get_prisma)
) -> Dict[str, Any]:
    """
    Create GraphQL context with database connection and request information.

    Args:
        request: FastAPI request object
        database: Database connection from dependency injection

    Returns:
        Dict[str, Any]: Context dictionary for GraphQL operations
    """
    try:
        # Extract user information from request headers or authentication
        user = None

        # Check for authentication headers (if authentication is implemented)
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # TODO: Implement JWT token validation or other auth methods
            # For now, we'll just log that auth was attempted
            logger.info(
                f"GraphQL request with authorization header: {auth_header[:20]}..."
            )

        # Extract client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")

        logger.debug(f"GraphQL request from {client_ip} with user agent: {user_agent}")

        return {
            "request": request,
            "database": database,
            "user": user,
            "client_ip": client_ip,
            "user_agent": user_agent,
        }

    except Exception as e:
        logger.error(f"Error creating GraphQL context: {str(e)}")
        raise


async def get_authenticated_context(
    context: Dict[str, Any] = Depends(get_graphql_context)
) -> Dict[str, Any]:
    """
    Get GraphQL context with authentication validation.

    This can be used as a dependency for resolvers that require authentication.

    Args:
        context: Base GraphQL context

    Returns:
        Dict[str, Any]: Authenticated context

    Raises:
        Exception: If authentication fails
    """
    # TODO: Implement authentication validation
    # For now, we'll just return the context as-is
    # In a real implementation, you would:
    # 1. Validate JWT tokens
    # 2. Check user permissions
    # 3. Populate the user field with authenticated user data

    if not context.get("user"):
        # For development, we'll allow unauthenticated access
        # In production, you might want to raise an authentication error
        logger.debug("GraphQL request without authentication")

    return context


class GraphQLPermissions:
    """Permission checks for GraphQL operations."""

    @staticmethod
    def can_read_portfolios(context: Dict[str, Any]) -> bool:
        """Check if user can read portfolios."""
        # TODO: Implement permission logic
        return True

    @staticmethod
    def can_write_portfolios(context: Dict[str, Any]) -> bool:
        """Check if user can modify portfolios."""
        # TODO: Implement permission logic
        return True

    @staticmethod
    def can_execute_analysis(context: Dict[str, Any]) -> bool:
        """Check if user can execute analysis."""
        # TODO: Implement permission logic
        return True

    @staticmethod
    def can_access_system_data(context: Dict[str, Any]) -> bool:
        """Check if user can access system-level data."""
        # TODO: Implement permission logic
        return True


def require_permission(permission_func):
    """Decorator to require specific permissions for GraphQL resolvers."""

    def decorator(resolver_func):
        async def wrapper(*args, **kwargs):
            # Extract context from arguments
            context = None
            for arg in args:
                if isinstance(arg, dict) and "request" in arg:
                    context = arg
                    break

            if not context:
                raise Exception("GraphQL context not found")

            if not permission_func(context):
                raise Exception("Insufficient permissions")

            return await resolver_func(*args, **kwargs)

        return wrapper

    return decorator


# Permission decorators for common use cases
require_read_portfolios = require_permission(GraphQLPermissions.can_read_portfolios)
require_write_portfolios = require_permission(GraphQLPermissions.can_write_portfolios)
require_execute_analysis = require_permission(GraphQLPermissions.can_execute_analysis)
require_system_access = require_permission(GraphQLPermissions.can_access_system_data)

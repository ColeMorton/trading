"""
GraphQL Error Handling

This module provides custom error handling for GraphQL operations.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

import strawberry

from app.api.utils.logging import setup_api_logging

# Set up logging
log, _, logger, _ = setup_api_logging()


@strawberry.enum
class GraphQLErrorCode(Enum):
    """GraphQL error codes for client handling."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_ERROR = "SERVICE_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"


@strawberry.type
class GraphQLError:
    """Custom GraphQL error type with enhanced information."""

    message: str
    code: GraphQLErrorCode
    path: Optional[List[str]] | None = None
    extensions: Optional[Dict[str, Any]] = None


class ValidationError(Exception):
    """Validation error for GraphQL operations."""

    def __init__(self, message: str, field: Optional[str] | None = None):
        self.message = message
        self.field = field
        super().__init__(message)


class AuthenticationError(Exception):
    """Authentication error for GraphQL operations."""

    def __init__(self, message: str = "Authentication required"):
        self.message = message
        super().__init__(message)


class AuthorizationError(Exception):
    """Authorization error for GraphQL operations."""

    def __init__(self, message: str = "Insufficient permissions"):
        self.message = message
        super().__init__(message)


class NotFoundError(Exception):
    """Not found error for GraphQL operations."""

    def __init__(self, resource: str, identifier: str):
        self.message = f"{resource} with identifier '{identifier}' not found"
        self.resource = resource
        self.identifier = identifier
        super().__init__(self.message)


class DatabaseError(Exception):
    """Database error for GraphQL operations."""

    def __init__(self, message: str, operation: Optional[str] | None = None):
        self.message = message
        self.operation = operation
        super().__init__(message)


class ServiceError(Exception):
    """Service error for GraphQL operations."""

    def __init__(self, message: str, service: Optional[str] | None = None):
        self.message = message
        self.service = service
        super().__init__(message)


def format_graphql_error(
    error: Exception, path: Optional[List[str]] | None = None
) -> Dict[str, Any]:
    """
    Format an exception into a GraphQL error response.

    Args:
        error: The exception to format
        path: The GraphQL path where the error occurred

    Returns:
        Dictionary containing formatted error information
    """
    error_info = {"message": str(error), "path": path, "extensions": {}}

    # Determine error code and add specific information
    if isinstance(error, ValidationError):
        error_info["extensions"]["code"] = GraphQLErrorCode.VALIDATION_ERROR.value
        if hasattr(error, "field") and error.field:
            error_info["extensions"]["field"] = error.field

    elif isinstance(error, AuthenticationError):
        error_info["extensions"]["code"] = GraphQLErrorCode.AUTHENTICATION_ERROR.value

    elif isinstance(error, AuthorizationError):
        error_info["extensions"]["code"] = GraphQLErrorCode.AUTHORIZATION_ERROR.value

    elif isinstance(error, NotFoundError):
        error_info["extensions"]["code"] = GraphQLErrorCode.NOT_FOUND.value
        if hasattr(error, "resource"):
            error_info["extensions"]["resource"] = error.resource
        if hasattr(error, "identifier"):
            error_info["extensions"]["identifier"] = error.identifier

    elif isinstance(error, DatabaseError):
        error_info["extensions"]["code"] = GraphQLErrorCode.DATABASE_ERROR.value
        if hasattr(error, "operation") and error.operation:
            error_info["extensions"]["operation"] = error.operation

    elif isinstance(error, ServiceError):
        error_info["extensions"]["code"] = GraphQLErrorCode.SERVICE_ERROR.value
        if hasattr(error, "service") and error.service:
            error_info["extensions"]["service"] = error.service

    else:
        # Generic internal error
        error_info["extensions"]["code"] = GraphQLErrorCode.INTERNAL_ERROR.value

        # Log internal errors for debugging
        logger.error(f"GraphQL internal error: {str(error)}", exc_info=True)

    return error_info


def handle_resolver_errors(resolver_func):
    """
    Decorator to handle errors in GraphQL resolvers.

    This decorator catches common exceptions and converts them to appropriate
    GraphQL error responses.
    """

    async def wrapper(*args, **kwargs):
        try:
            return await resolver_func(*args, **kwargs)

        except (
            ValidationError,
            AuthenticationError,
            AuthorizationError,
            NotFoundError,
            DatabaseError,
            ServiceError,
        ) as e:
            # Re-raise known errors to be handled by GraphQL error formatter
            raise e

        except Exception as e:
            # Log unexpected errors and convert to generic error
            logger.error(
                f"Unexpected error in GraphQL resolver {resolver_func.__name__}: {str(e)}",
                exc_info=True,
            )
            raise ServiceError(
                f"An unexpected error occurred in {resolver_func.__name__}"
            )

    return wrapper


class ErrorLogger:
    """Utility class for logging GraphQL errors with context."""

    @staticmethod
    def log_validation_error(error: ValidationError, context: Any | None = None):
        """Log validation error with context."""
        logger.warning(f"GraphQL validation error: {error.message}")
        if hasattr(error, "field") and error.field:
            logger.warning(f"  Field: {error.field}")

    @staticmethod
    def log_authentication_error(
        error: AuthenticationError, context: Any | None = None
    ):
        """Log authentication error with context."""
        client_ip = "unknown"
        if context and hasattr(context, "request") and context.request.client:
            client_ip = context.request.client.host
        logger.warning(
            f"GraphQL authentication error from {client_ip}: {error.message}"
        )

    @staticmethod
    def log_authorization_error(error: AuthorizationError, context: Any | None = None):
        """Log authorization error with context."""
        user_info = "anonymous"
        if context and hasattr(context, "user") and context.user:
            user_info = context.user.get("id", "unknown")
        logger.warning(
            f"GraphQL authorization error for user {user_info}: {error.message}"
        )

    @staticmethod
    def log_database_error(error: DatabaseError, context: Any | None = None):
        """Log database error with context."""
        logger.error(f"GraphQL database error: {error.message}")
        if hasattr(error, "operation") and error.operation:
            logger.error(f"  Operation: {error.operation}")

    @staticmethod
    def log_service_error(error: ServiceError, context: Any | None = None):
        """Log service error with context."""
        logger.error(f"GraphQL service error: {error.message}")
        if hasattr(error, "service") and error.service:
            logger.error(f"  Service: {error.service}")


# Error handler mapping for automatic logging
ERROR_LOGGERS = {
    ValidationError: ErrorLogger.log_validation_error,
    AuthenticationError: ErrorLogger.log_authentication_error,
    AuthorizationError: ErrorLogger.log_authorization_error,
    DatabaseError: ErrorLogger.log_database_error,
    ServiceError: ErrorLogger.log_service_error,
}

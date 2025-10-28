"""
Automated resource cleanup framework to prevent test pollution.
Phase 3: Testing Infrastructure Consolidation
"""

from collections.abc import Callable
from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import tempfile
import threading
import time
from typing import Any

import pytest


class ResourceCleanupManager:
    """
    Automated resource cleanup manager that tracks and cleans up test resources
    to prevent test pollution and resource leaks.
    """

    def __init__(self):
        self.tracked_resources: dict[str, dict[str, Any]] = {}
        self.cleanup_handlers: dict[str, Callable] = {}
        self.temp_directories: set[Path] = set()
        self.temp_files: set[Path] = set()
        self.mock_objects: set[Any] = set()
        self.database_sessions: list[Any] = []
        self.network_connections: list[Any] = []
        self._lock = threading.Lock()

    def register_resource(
        self,
        resource_id: str,
        resource: Any,
        cleanup_func: Callable,
        resource_type: str = "generic",
    ):
        """
        Register a resource for automatic cleanup.

        Args:
            resource_id: Unique identifier for the resource
            resource: The resource object
            cleanup_func: Function to clean up the resource
            resource_type: Type of resource (file, database, network, etc.)
        """
        with self._lock:
            self.tracked_resources[resource_id] = {
                "resource": resource,
                "cleanup_func": cleanup_func,
                "type": resource_type,
                "created_at": time.time(),
                "test_name": self._get_current_test_name(),
            }

    def _get_current_test_name(self) -> str:
        """Get the current test name from pytest context."""
        import inspect

        frame = inspect.currentframe()
        while frame:
            if "test_" in frame.f_code.co_name:
                return frame.f_code.co_name
            frame = frame.f_back
        return "unknown_test"

    def register_temp_directory(self, directory: Path) -> Path:
        """Register temporary directory for cleanup."""
        self.temp_directories.add(directory)
        return directory

    def register_temp_file(self, file_path: Path) -> Path:
        """Register temporary file for cleanup."""
        self.temp_files.add(file_path)
        return file_path

    def register_mock_object(self, mock_obj: Any) -> Any:
        """Register mock object for cleanup."""
        self.mock_objects.add(mock_obj)
        return mock_obj

    def register_database_session(self, session: Any) -> Any:
        """Register database session for cleanup."""
        self.database_sessions.append(session)
        return session

    def cleanup_resource(self, resource_id: str) -> bool:
        """
        Clean up a specific resource.

        Args:
            resource_id: ID of resource to clean up

        Returns:
            True if cleanup successful, False otherwise
        """
        with self._lock:
            if resource_id not in self.tracked_resources:
                return False

            resource_info = self.tracked_resources[resource_id]
            try:
                resource_info["cleanup_func"](resource_info["resource"])
                del self.tracked_resources[resource_id]
                return True
            except Exception as e:
                print(f"Warning: Failed to cleanup resource {resource_id}: {e}")
                return False

    def cleanup_all_resources(self, resource_type: str | None = None):
        """
        Clean up all tracked resources, optionally filtered by type.

        Args:
            resource_type: Only clean up resources of this type (None for all)
        """
        with self._lock:
            resources_to_cleanup = list(self.tracked_resources.items())

        for resource_id, resource_info in resources_to_cleanup:
            if resource_type is None or resource_info["type"] == resource_type:
                self.cleanup_resource(resource_id)

        # Clean up other tracked resources
        self._cleanup_temp_directories()
        self._cleanup_temp_files()
        self._cleanup_mock_objects()
        self._cleanup_database_sessions()

    def _cleanup_temp_directories(self):
        """Clean up all temporary directories."""
        for directory in list(self.temp_directories):
            try:
                if directory.exists():
                    shutil.rmtree(directory)
                self.temp_directories.remove(directory)
            except Exception as e:
                print(f"Warning: Failed to cleanup temp directory {directory}: {e}")

    def _cleanup_temp_files(self):
        """Clean up all temporary files."""
        for file_path in list(self.temp_files):
            try:
                if file_path.exists():
                    file_path.unlink()
                self.temp_files.remove(file_path)
            except Exception as e:
                print(f"Warning: Failed to cleanup temp file {file_path}: {e}")

    def _cleanup_mock_objects(self):
        """Clean up all mock objects."""
        for mock_obj in list(self.mock_objects):
            try:
                if hasattr(mock_obj, "reset_mock"):
                    mock_obj.reset_mock()
                if hasattr(mock_obj, "stop"):
                    mock_obj.stop()
            except Exception as e:
                print(f"Warning: Failed to cleanup mock object: {e}")
        self.mock_objects.clear()

    def _cleanup_database_sessions(self):
        """Clean up all database sessions."""
        for session in list(self.database_sessions):
            try:
                if hasattr(session, "rollback"):
                    session.rollback()
                if hasattr(session, "close"):
                    session.close()
            except Exception as e:
                print(f"Warning: Failed to cleanup database session: {e}")
        self.database_sessions.clear()

    def get_resource_stats(self) -> dict[str, Any]:
        """Get statistics about tracked resources."""
        with self._lock:
            total_resources = len(self.tracked_resources)
            resource_types = {}

            for resource_info in self.tracked_resources.values():
                resource_type = resource_info["type"]
                resource_types[resource_type] = resource_types.get(resource_type, 0) + 1

            return {
                "total_tracked_resources": total_resources,
                "resource_types": resource_types,
                "temp_directories": len(self.temp_directories),
                "temp_files": len(self.temp_files),
                "mock_objects": len(self.mock_objects),
                "database_sessions": len(self.database_sessions),
            }


# Global cleanup manager
_cleanup_manager = ResourceCleanupManager()


def get_cleanup_manager() -> ResourceCleanupManager:
    """Get the global cleanup manager instance."""
    return _cleanup_manager


# =============================================================================
# Cleanup decorators and context managers
# =============================================================================


def auto_cleanup(resource_type: str = "generic"):
    """
    Decorator for automatic resource cleanup.

    Args:
        resource_type: Type of resource being created
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            resource = func(*args, **kwargs)

            # Auto-register common resource types
            if hasattr(resource, "close"):
                cleanup_manager = get_cleanup_manager()
                resource_id = f"{func.__name__}_{id(resource)}"
                cleanup_manager.register_resource(
                    resource_id, resource, lambda r: r.close(), resource_type,
                )

            return resource

        return wrapper

    return decorator


@contextmanager
def managed_temp_directory(prefix: str = "test_"):
    """Context manager for temporary directory with automatic cleanup."""
    cleanup_manager = get_cleanup_manager()
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    cleanup_manager.register_temp_directory(temp_dir)

    try:
        yield temp_dir
    finally:
        # Cleanup is handled by the cleanup manager
        pass


@contextmanager
def managed_temp_file(suffix: str = ".tmp", prefix: str = "test_"):
    """Context manager for temporary file with automatic cleanup."""
    cleanup_manager = get_cleanup_manager()
    fd, temp_file_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)  # Close the file descriptor

    temp_path = Path(temp_file_path)
    cleanup_manager.register_temp_file(temp_path)

    try:
        yield temp_path
    finally:
        # Cleanup is handled by the cleanup manager
        pass


@contextmanager
def managed_mock(mock_obj: Any):
    """Context manager for mock object with automatic cleanup."""
    cleanup_manager = get_cleanup_manager()
    cleanup_manager.register_mock_object(mock_obj)

    try:
        yield mock_obj
    finally:
        # Cleanup is handled by the cleanup manager
        pass


# =============================================================================
# Pytest fixtures for automatic cleanup
# =============================================================================


@pytest.fixture(autouse=True, scope="function")
def auto_resource_cleanup():
    """Automatic resource cleanup for each test function."""
    yield
    # Clean up all resources after each test
    cleanup_manager = get_cleanup_manager()
    cleanup_manager.cleanup_all_resources()


@pytest.fixture(scope="session")
def cleanup_manager():
    """Provide cleanup manager instance for tests."""
    return get_cleanup_manager()


@pytest.fixture
def temp_directory():
    """Managed temporary directory fixture."""
    with managed_temp_directory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_file():
    """Managed temporary file fixture."""
    with managed_temp_file() as temp_file:
        yield temp_file


# =============================================================================
# Resource-specific cleanup utilities
# =============================================================================


class DatabaseCleanup:
    """Database-specific cleanup utilities."""

    @staticmethod
    def cleanup_test_tables(session, table_names: list[str]):
        """Clean up specific test tables."""
        for table_name in table_names:
            try:
                session.execute(f"DELETE FROM {table_name}")
                session.commit()
            except Exception as e:
                print(f"Warning: Failed to cleanup table {table_name}: {e}")
                session.rollback()

    @staticmethod
    def cleanup_test_data(session, cleanup_queries: list[str]):
        """Execute cleanup queries."""
        for query in cleanup_queries:
            try:
                session.execute(query)
                session.commit()
            except Exception as e:
                print(f"Warning: Failed to execute cleanup query: {e}")
                session.rollback()


class FileSystemCleanup:
    """File system cleanup utilities."""

    @staticmethod
    def cleanup_csv_files(directory: Path, pattern: str = "test_*.csv"):
        """Clean up CSV files matching pattern."""
        for csv_file in directory.glob(pattern):
            try:
                csv_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to cleanup CSV file {csv_file}: {e}")

    @staticmethod
    def cleanup_log_files(directory: Path, pattern: str = "test_*.log"):
        """Clean up log files matching pattern."""
        for log_file in directory.glob(pattern):
            try:
                log_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to cleanup log file {log_file}: {e}")


class NetworkCleanup:
    """Network resource cleanup utilities."""

    @staticmethod
    def cleanup_mock_responses():
        """Clean up any persistent mock HTTP responses."""
        try:
            import responses

            responses.reset()
        except ImportError:
            pass

    @staticmethod
    def cleanup_requests_cache():
        """Clean up requests cache if present."""
        try:
            import requests_cache

            requests_cache.clear()
        except ImportError:
            pass

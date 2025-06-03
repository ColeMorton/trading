"""Project utilities.

This module provides utilities for working with project paths and directories.
"""
import os
from pathlib import Path


def get_project_root() -> str:
    """Get the absolute path to the project root directory.

    Returns:
        Absolute path to the project root directory
    """
    # Start from the current file and go up to the project root
    current_file = os.path.abspath(__file__)
    tools_dir = os.path.dirname(current_file)
    app_dir = os.path.dirname(tools_dir)
    project_root = os.path.dirname(app_dir)

    return project_root


def resolve_path(path: str, base_dir: str = None) -> str:
    """Resolve a path relative to a base directory.

    Args:
        path: Path to resolve
        base_dir: Base directory (defaults to project root)

    Returns:
        Absolute path
    """
    if os.path.isabs(path):
        return path

    if base_dir is None:
        base_dir = get_project_root()

    return os.path.abspath(os.path.join(base_dir, path))

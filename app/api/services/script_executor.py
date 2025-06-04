"""
Script Execution Service

This module provides functionality for executing Python scripts.
It supports both synchronous and asynchronous execution.
"""

import asyncio
import importlib.util
import logging
import os
import sys
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Tuple

from app.api.config import get_config
from app.tools.setup_logging import setup_logging

# Dictionary to store task status for async execution
task_status = {}


class ScriptExecutionError(Exception):
    """Exception raised for errors during script execution."""


def import_script_module(script_path: str) -> Any:
    """
    Import a Python script as a module.

    Args:
        script_path (str): Path to the script

    Returns:
        Any: The imported module

    Raises:
        ScriptExecutionError: If the script cannot be imported
    """
    try:
        config = get_config()
        full_path = os.path.join(config["BASE_DIR"], script_path)

        # Get the module name from the file path
        module_name = os.path.splitext(os.path.basename(script_path))[0]

        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        if spec is None or spec.loader is None:
            raise ScriptExecutionError(f"Failed to load spec for {script_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        return module
    except Exception as e:
        raise ScriptExecutionError(f"Failed to import script {script_path}: {str(e)}")


def execute_script_sync(script_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a script synchronously.

    Args:
        script_path (str): Path to the script
        parameters (Dict[str, Any]): Parameters to pass to the script

    Returns:
        Dict[str, Any]: Result of the script execution

    Raises:
        ScriptExecutionError: If the script execution fails
    """
    log, log_close, _, _ = setup_logging(
        module_name="api",
        log_file=f"script_execution_{os.path.basename(script_path)}.log",
        log_subdir="scripts",
    )

    try:
        log(f"Executing script {script_path} with parameters: {parameters}")

        # Import the script module
        module = import_script_module(script_path)

        # Check if the module has a run function
        if not hasattr(module, "run"):
            raise ScriptExecutionError(
                f"Script {script_path} does not have a run function"
            )

        # Execute the run function with parameters
        start_time = time.time()
        result = module.run(**parameters)
        execution_time = time.time() - start_time

        log(f"Script execution completed in {execution_time:.2f} seconds")
        log(f"Result: {result}")

        # Close logging
        log_close()

        return {
            "success": True,
            "message": f"Script executed successfully in {execution_time:.2f} seconds",
            "execution_time": execution_time,
            "data": result,
        }
    except Exception as e:
        error_message = f"Script execution failed: {str(e)}"
        log(error_message, "error")
        log(traceback.format_exc(), "error")
        log_close()

        return {
            "success": False,
            "message": error_message,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


async def execute_script_async(
    script_path: str, parameters: Dict[str, Any], execution_id: str
) -> None:
    """
    Execute a script asynchronously.

    Args:
        script_path (str): Path to the script
        parameters (Dict[str, Any]): Parameters to pass to the script
        execution_id (str): Unique identifier for the execution
    """
    log, log_close, _, _ = setup_logging(
        module_name="api",
        log_file=f"script_execution_{execution_id}.log",
        log_subdir="scripts",
    )

    # Update task status to running
    task_status[execution_id]["status"] = "running"
    task_status[execution_id]["message"] = f"Executing script {script_path}"
    task_status[execution_id]["progress"] = 10

    try:
        log(f"Executing script {script_path} with parameters: {parameters}")

        # Update progress before execution
        task_status[execution_id]["progress"] = 25
        task_status[execution_id]["message"] = f"Preparing to execute {script_path}"

        # Execute the script in a separate thread to avoid blocking the event loop
        with ThreadPoolExecutor() as executor:
            # Update progress before execution
            task_status[execution_id]["progress"] = 50
            task_status[execution_id]["message"] = f"Executing {script_path}"

            result = await asyncio.get_event_loop().run_in_executor(
                executor, execute_script_sync, script_path, parameters
            )

        # Update progress after execution
        task_status[execution_id]["progress"] = 90
        task_status[execution_id]["message"] = f"Finalizing results"

        # Update task status with result
        task_status[execution_id]["status"] = (
            "completed" if result["success"] else "failed"
        )
        task_status[execution_id]["progress"] = 100
        task_status[execution_id]["message"] = result["message"]
        task_status[execution_id]["result"] = result

        if not result["success"]:
            task_status[execution_id]["error"] = result["error"]

        log(
            f"Async script execution completed with status: {
    task_status[execution_id]['status']}"
        )
        log(f"Result: {result}")

    except Exception as e:
        error_message = f"Async script execution failed: {str(e)}"
        log(error_message, "error")
        log(traceback.format_exc(), "error")

        # Update task status with error
        task_status[execution_id]["status"] = "failed"
        task_status[execution_id]["message"] = error_message
        task_status[execution_id]["error"] = str(e)
        task_status[execution_id]["progress"] = 100

    # Update end time
    task_status[execution_id]["end_time"] = datetime.now()

    # Close logging
    log_close()


def start_script_execution(
    script_path: str, parameters: Dict[str, Any], async_execution: bool = False
) -> Tuple[str, Dict[str, Any]]:
    """
    Start script execution, either synchronously or asynchronously.

    Args:
        script_path (str): Path to the script
        parameters (Dict[str, Any]): Parameters to pass to the script
        async_execution (bool): Whether to execute the script asynchronously

    Returns:
        Tuple[str, Dict[str, Any]]: Execution ID and result (for sync) or status (for async)
    """
    # Generate a unique execution ID
    execution_id = str(uuid.uuid4())

    if async_execution:
        # Initialize task status
        task_status[execution_id] = {
            "execution_id": execution_id,
            "status": "pending",
            "progress": 0,
            "message": "Script execution pending",
            "start_time": datetime.now(),
            "end_time": None,
            "result": None,
            "error": None,
        }

        # Start async execution
        asyncio.create_task(execute_script_async(script_path, parameters, execution_id))

        return execution_id, {
            "status": "accepted",
            "execution_id": execution_id,
            "message": "Script execution started",
        }
    else:
        # Execute synchronously
        result = execute_script_sync(script_path, parameters)
        return None, result


def get_script_status(execution_id: str) -> Dict[str, Any]:
    """
    Get the status of a script execution.

    Args:
        execution_id (str): Unique identifier for the execution

    Returns:
        Dict[str, Any]: Status of the script execution

    Raises:
        ValueError: If the execution ID is not found
    """
    if execution_id not in task_status:
        raise ValueError(f"Execution ID not found: {execution_id}")

    status_data = task_status[execution_id]

    # Calculate elapsed time
    start_time = status_data["start_time"]
    end_time = status_data["end_time"] or datetime.now()
    elapsed_time = (end_time - start_time).total_seconds()

    return {
        "execution_id": execution_id,
        "status": status_data["status"],
        "progress": status_data["progress"],
        "message": status_data["message"],
        "start_time": start_time,
        "elapsed_time": elapsed_time,
        "result": status_data["result"],
        "error": status_data["error"],
    }


def get_available_scripts() -> List[Dict[str, Any]]:
    """
    Get a list of available scripts that can be executed.

    Returns:
        List[Dict[str, Any]]: List of script information
    """
    config = get_config()
    scripts = []

    for script_dir in config["ALLOWED_SCRIPT_DIRS"]:
        full_dir_path = os.path.join(config["BASE_DIR"], script_dir)

        if not os.path.isdir(full_dir_path):
            continue

        for root, _, files in os.walk(full_dir_path):
            for file in files:
                if file.endswith(".py"):
                    # Get relative path from BASE_DIR
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, config["BASE_DIR"])

                    # Import the module to get docstring and other info
                    try:
                        module = import_script_module(rel_path)
                        description = module.__doc__.strip() if module.__doc__ else None

                        # Try to determine parameters from the run function
                        parameters = {}
                        if hasattr(module, "run"):
                            import inspect

                            sig = inspect.signature(module.run)
                            for param_name, param in sig.parameters.items():
                                param_type = "unknown"
                                if param.annotation != inspect.Parameter.empty:
                                    param_type = str(param.annotation)
                                parameters[param_name] = param_type

                        scripts.append(
                            {
                                "path": rel_path,
                                "description": description,
                                "parameters": parameters,
                            }
                        )
                    except Exception as e:
                        # Skip scripts that can't be imported
                        logging.warning(f"Failed to import script {rel_path}: {str(e)}")

    return scripts

"""
Data Service

This module provides functionality for retrieving and listing data files.
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Union, Optional
import pandas as pd

from app.api.config import get_config, is_path_allowed

class DataServiceError(Exception):
    """Exception raised for errors in the data service."""
    pass

def get_file_info(file_path: str, base_dir: str) -> Dict[str, Any]:
    """
    Get information about a file.
    
    Args:
        file_path (str): Path to the file
        base_dir (str): Base directory
        
    Returns:
        Dict[str, Any]: File information
        
    Raises:
        DataServiceError: If the file does not exist
    """
    full_path = os.path.join(base_dir, file_path)
    
    if not os.path.exists(full_path):
        raise DataServiceError(f"File does not exist: {file_path}")
    
    try:
        stat = os.stat(full_path)
        
        return {
            "path": file_path,
            "type": "directory" if os.path.isdir(full_path) else "file",
            "size": stat.st_size if os.path.isfile(full_path) else None,
            "last_modified": datetime.fromtimestamp(stat.st_mtime)
        }
    except Exception as e:
        raise DataServiceError(f"Failed to get file info for {file_path}: {str(e)}")

def list_files(directory: str) -> List[Dict[str, Any]]:
    """
    List files in a directory.
    
    Args:
        directory (str): Directory to list
        
    Returns:
        List[Dict[str, Any]]: List of file information
        
    Raises:
        DataServiceError: If the directory does not exist or is not allowed
    """
    config = get_config()
    base_dir = config["BASE_DIR"]
    
    # If directory is just 'csv' or 'json', use it directly
    if directory in config["ALLOWED_DATA_DIRS"]:
        pass
    # If directory already starts with an allowed directory, use it as is
    elif any(directory.startswith(d + '/') for d in config["ALLOWED_DATA_DIRS"]):
        pass
    # Otherwise, check if it's a subdirectory of an allowed directory
    else:
        # Try to find which allowed directory it might be in
        found = False
        for allowed_dir in config["ALLOWED_DATA_DIRS"]:
            test_path = os.path.join(allowed_dir, directory)
            if os.path.isdir(os.path.join(base_dir, test_path)):
                directory = test_path
                found = True
                break
        
        if not found:
            # Default to csv if not found
            directory = os.path.join('csv', directory)
    
    # Check if the directory is allowed
    if not is_path_allowed(directory, config["ALLOWED_DATA_DIRS"], base_dir):
        allowed_dirs = ", ".join(config["ALLOWED_DATA_DIRS"])
        raise DataServiceError(f"Directory must be within allowed directories: {allowed_dirs}")
    
    full_path = os.path.join(base_dir, directory)
    
    if not os.path.isdir(full_path):
        raise DataServiceError(f"Directory does not exist: {directory}")
    
    try:
        files = []
        
        for item in os.listdir(full_path):
            item_path = os.path.join(directory, item)
            files.append(get_file_info(item_path, base_dir))
        
        return files
    except Exception as e:
        raise DataServiceError(f"Failed to list files in {directory}: {str(e)}")

def read_csv_file(file_path: str) -> Dict[str, Any]:
    """
    Read a CSV file.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        Dict[str, Any]: CSV data
        
    Raises:
        DataServiceError: If the file cannot be read
    """
    config = get_config()
    base_dir = config["BASE_DIR"]
    
    # Handle paths that might already include the allowed directory
    if not any(file_path.startswith(d + '/') or file_path == d for d in config["ALLOWED_DATA_DIRS"]):
        # If the path doesn't already include the allowed directory, prepend 'csv/'
        file_path = os.path.join('csv', file_path)
    
    # Check if the file is allowed
    if not is_path_allowed(file_path, config["ALLOWED_DATA_DIRS"], base_dir):
        allowed_dirs = ", ".join(config["ALLOWED_DATA_DIRS"])
        raise DataServiceError(f"File must be within allowed directories: {allowed_dirs}")
    
    full_path = os.path.join(base_dir, file_path)
    
    if not os.path.isfile(full_path):
        raise DataServiceError(f"File does not exist: {file_path}")
    
    if not file_path.endswith('.csv'):
        raise DataServiceError(f"File is not a CSV file: {file_path}")
    
    try:
        # Read CSV file using pandas for better handling of various CSV formats
        df = pd.read_csv(full_path)
        
        # Convert to dict for JSON serialization
        records = df.to_dict(orient='records')
        columns = df.columns.tolist()
        
        return {
            "data": records,
            "columns": columns,
            "row_count": len(records),
            "column_count": len(columns)
        }
    except Exception as e:
        raise DataServiceError(f"Failed to read CSV file {file_path}: {str(e)}")

def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    Read a JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        Dict[str, Any]: JSON data
        
    Raises:
        DataServiceError: If the file cannot be read
    """
    config = get_config()
    base_dir = config["BASE_DIR"]
    
    # Handle paths that might already include the allowed directory
    if not any(file_path.startswith(d + '/') or file_path == d for d in config["ALLOWED_DATA_DIRS"]):
        # If the path doesn't already include the allowed directory, prepend 'json/'
        file_path = os.path.join('json', file_path)
    
    # Check if the file is allowed
    if not is_path_allowed(file_path, config["ALLOWED_DATA_DIRS"], base_dir):
        allowed_dirs = ", ".join(config["ALLOWED_DATA_DIRS"])
        raise DataServiceError(f"File must be within allowed directories: {allowed_dirs}")
    
    full_path = os.path.join(base_dir, file_path)
    
    if not os.path.isfile(full_path):
        raise DataServiceError(f"File does not exist: {file_path}")
    
    if not file_path.endswith('.json'):
        raise DataServiceError(f"File is not a JSON file: {file_path}")
    
    try:
        with open(full_path, 'r') as f:
            data = json.load(f)
        
        return {
            "data": data
        }
    except Exception as e:
        raise DataServiceError(f"Failed to read JSON file {file_path}: {str(e)}")

def read_ticker_lists() -> Dict[str, List[str]]:
    """
    Read all ticker lists from the json/ticker_lists directory.
    
    Returns:
        Dict[str, List[str]]: Dictionary mapping list names to ticker arrays
        
    Raises:
        DataServiceError: If ticker lists cannot be read
    """
    config = get_config()
    base_dir = config["BASE_DIR"]
    ticker_lists_dir = "json/ticker_lists"
    
    # Check if the directory is allowed
    if not is_path_allowed(ticker_lists_dir, config["ALLOWED_DATA_DIRS"], base_dir):
        allowed_dirs = ", ".join(config["ALLOWED_DATA_DIRS"])
        raise DataServiceError(f"Directory must be within allowed directories: {allowed_dirs}")
    
    full_path = os.path.join(base_dir, ticker_lists_dir)
    
    if not os.path.isdir(full_path):
        raise DataServiceError(f"Ticker lists directory does not exist: {ticker_lists_dir}")
    
    try:
        ticker_lists = {}
        
        # Read all JSON files in the ticker_lists directory
        for item in os.listdir(full_path):
            if item.endswith('.json'):
                list_name = item[:-5]  # Remove .json extension
                file_path = os.path.join(full_path, item)
                
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Validate that the JSON contains a list of strings
                    if not isinstance(data, list):
                        raise DataServiceError(f"Ticker list {list_name} must be an array")
                    
                    # Validate that all items are strings
                    for ticker in data:
                        if not isinstance(ticker, str):
                            raise DataServiceError(f"All tickers in {list_name} must be strings")
                    
                    ticker_lists[list_name] = data
                    
                except json.JSONDecodeError as e:
                    raise DataServiceError(f"Invalid JSON in ticker list {list_name}: {str(e)}")
                except Exception as e:
                    raise DataServiceError(f"Failed to read ticker list {list_name}: {str(e)}")
        
        return ticker_lists
        
    except Exception as e:
        if isinstance(e, DataServiceError):
            raise e
        raise DataServiceError(f"Failed to read ticker lists: {str(e)}")

def read_data_file(file_path: str, file_format: Optional[str] = None) -> Dict[str, Any]:
    """
    Read a data file.
    
    Args:
        file_path (str): Path to the data file
        file_format (Optional[str]): Format of the file (csv, json)
        
    Returns:
        Dict[str, Any]: File data
        
    Raises:
        DataServiceError: If the file cannot be read
    """
    # Determine format from file extension if not provided
    if file_format is None:
        if file_path.endswith('.csv'):
            file_format = 'csv'
        elif file_path.endswith('.json'):
            file_format = 'json'
        else:
            raise DataServiceError(f"Cannot determine format for file: {file_path}")
    
    # Read file based on format
    if file_format == 'csv':
        return read_csv_file(file_path)
    elif file_format == 'json':
        return read_json_file(file_path)
    else:
        raise DataServiceError(f"Unsupported file format: {file_format}")
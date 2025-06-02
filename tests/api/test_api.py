"""
API Server Test Script

This script tests the API server by making requests to various endpoints.
"""

import requests
import json
import time
import argparse
from typing import Dict, Any, List, Optional

def test_root(base_url: str) -> bool:
    """
    Test the root endpoint.
    
    Args:
        base_url (str): Base URL of the API server
        
    Returns:
        bool: True if the test passed, False otherwise
    """
    print("\n=== Testing Root Endpoint ===")
    
    try:
        response = requests.get(f"{base_url}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_health(base_url: str) -> bool:
    """
    Test the health endpoint.
    
    Args:
        base_url (str): Base URL of the API server
        
    Returns:
        bool: True if the test passed, False otherwise
    """
    print("\n=== Testing Health Endpoint ===")
    
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_list_scripts(base_url: str) -> bool:
    """
    Test the list scripts endpoint.
    
    Args:
        base_url (str): Base URL of the API server
        
    Returns:
        bool: True if the test passed, False otherwise
    """
    print("\n=== Testing List Scripts Endpoint ===")
    
    try:
        response = requests.get(f"{base_url}/api/scripts/list")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data['scripts'])} scripts")
            
            # Print first 3 scripts
            for i, script in enumerate(data['scripts'][:3]):
                print(f"Script {i+1}: {script['path']}")
                if script.get('description'):
                    print(f"  Description: {script['description'][:50]}...")
                print(f"  Parameters: {list(script['parameters'].keys())}")
            
            return True
        else:
            print(f"Response: {response.json()}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_list_data(base_url: str) -> bool:
    """
    Test the list data endpoint.
    
    Args:
        base_url (str): Base URL of the API server
        
    Returns:
        bool: True if the test passed, False otherwise
    """
    print("\n=== Testing List Data Endpoint ===")
    
    try:
        response = requests.get(f"{base_url}/api/data/list")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data['files'])} files in {data['directory']}")
            
            # Print first 3 files
            for i, file in enumerate(data['files'][:3]):
                print(f"File {i+1}: {file['path']}")
                print(f"  Type: {file['type']}")
                if file['size']:
                    print(f"  Size: {file['size']} bytes")
                print(f"  Last Modified: {file['last_modified']}")
            
            return True
        else:
            print(f"Response: {response.json()}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_get_csv_data(base_url: str, csv_path: str) -> bool:
    """
    Test the get CSV data endpoint.
    
    Args:
        base_url (str): Base URL of the API server
        csv_path (str): Path to the CSV file
        
    Returns:
        bool: True if the test passed, False otherwise
    """
    print(f"\n=== Testing Get CSV Data Endpoint ({csv_path}) ===")
    
    try:
        response = requests.get(f"{base_url}/api/data/csv/{csv_path.replace('csv/', '')}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Format: {data['format']}")
            
            if 'data' in data and 'data' in data['data']:
                rows = data['data']['data']
                print(f"Found {len(rows)} rows")
                
                # Print first 3 rows
                for i, row in enumerate(rows[:3]):
                    print(f"Row {i+1}: {row}")
            
            return True
        else:
            print(f"Response: {response.json()}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_execute_script(base_url: str, script_path: str, parameters: Dict[str, Any], async_execution: bool) -> Optional[str]:
    """
    Test the execute script endpoint.
    
    Args:
        base_url (str): Base URL of the API server
        script_path (str): Path to the script
        parameters (Dict[str, Any]): Parameters for the script
        async_execution (bool): Whether to execute the script asynchronously
        
    Returns:
        Optional[str]: Execution ID if async, None otherwise
    """
    print(f"\n=== Testing Execute Script Endpoint ({script_path}) ===")
    print(f"Async: {async_execution}")
    print(f"Parameters: {parameters}")
    
    try:
        payload = {
            "script_path": script_path,
            "async_execution": async_execution,
            "parameters": parameters
        }
        
        response = requests.post(
            f"{base_url}/api/scripts/execute",
            json=payload
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if async_execution and response.status_code == 202:
            return data.get("execution_id")
        
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_script_status(base_url: str, execution_id: str, max_attempts: int = 10) -> bool:
    """
    Test the script status endpoint.
    
    Args:
        base_url (str): Base URL of the API server
        execution_id (str): Execution ID
        max_attempts (int): Maximum number of status check attempts
        
    Returns:
        bool: True if the test passed, False otherwise
    """
    print(f"\n=== Testing Script Status Endpoint ({execution_id}) ===")
    
    attempts = 0
    while attempts < max_attempts:
        try:
            response = requests.get(f"{base_url}/api/scripts/status/{execution_id}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Status: {data['status']}")
                print(f"Progress: {data['progress']}")
                print(f"Message: {data['message']}")
                print(f"Elapsed Time: {data['elapsed_time']:.2f} seconds")
                
                if data['status'] in ['completed', 'failed']:
                    if data['status'] == 'completed':
                        print("Script execution completed successfully")
                        if data.get('result'):
                            print(f"Result: {data['result']}")
                    else:
                        print(f"Script execution failed: {data.get('error')}")
                    
                    return data['status'] == 'completed'
            else:
                print(f"Response: {response.json()}")
                return False
        except Exception as e:
            print(f"Error: {str(e)}")
            return False
        
        attempts += 1
        print(f"Waiting for script to complete (attempt {attempts}/{max_attempts})...")
        time.sleep(5)
    
    print("Maximum attempts reached, script execution may still be in progress")
    return False

def main():
    """Run the API server tests."""
    parser = argparse.ArgumentParser(description="Test the API server")
    parser.add_argument("--host", default="127.0.0.1", help="API server host")
    parser.add_argument("--port", type=int, default=8000, help="API server port")
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    print(f"Testing API server at {base_url}")
    
    # Test basic endpoints
    test_root(base_url)
    test_health(base_url)
    
    # Test list endpoints
    test_list_scripts(base_url)
    test_list_data(base_url)
    
    # Test data retrieval
    test_get_csv_data(base_url, "csv/strategies/DAILY.csv")
    
    # Test script execution
    execution_id = test_execute_script(
        base_url,
        "app/ma_cross/1_get_portfolios.py",
        {
            "TICKER": ["NVDA", "NFLX"],
            "WINDOWS": 89,
            "DIRECTION": "Long"
        },
        True  # Async execution
    )
    
    if execution_id:
        test_script_status(base_url, execution_id)

if __name__ == "__main__":
    main()
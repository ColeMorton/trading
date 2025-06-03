"""
Simple API Server Test

This script makes a simple request to the API server to test if it's running.
"""

import requests


def main():
    """Make a simple request to the API server."""
    base_url = "http://127.0.0.1:8000"

    try:
        # Test the root endpoint
        print("\n=== Testing Root Endpoint ===")
        response = requests.get(f"{base_url}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        # Test the health endpoint
        print("\n=== Testing Health Endpoint ===")
        response = requests.get(f"{base_url}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        # Test the list scripts endpoint
        print("\n=== Testing List Scripts Endpoint ===")
        response = requests.get(f"{base_url}/api/scripts/list")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data['scripts'])} scripts")

        # Test the list data endpoint
        print("\n=== Testing List Data Endpoint ===")
        response = requests.get(f"{base_url}/api/data/list")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data['files'])} files in {data['directory']}")

        # Test the CSV data endpoint
        print("\n=== Testing CSV Data Endpoint ===")
        response = requests.get(f"{base_url}/api/data/csv/strategies/DAILY.csv")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Format: {data['format']}")
            if "data" in data and "data" in data["data"]:
                print(f"Found {len(data['data']['data'])} rows in CSV")

        print("\nAPI server is running!")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nAPI server is not running or not accessible.")


if __name__ == "__main__":
    main()

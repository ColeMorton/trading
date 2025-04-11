# Implementation Plan: Extending FastAPI Server for CSV Viewer

This document outlines the detailed implementation plan for extending the existing FastAPI server to serve the CSV viewer HTML file with hot reloading capabilities.

## Overview

We'll extend the existing FastAPI server in `app/api/` to:
1. Add static file serving capabilities
2. Create a new endpoint to serve the CSV viewer HTML file
3. Modify the HTML file to fetch CSV data from the API endpoints
4. Configure the server to enable hot reloading

## Detailed Implementation Steps

### 1. Add Static File Serving to FastAPI

First, we'll add static file serving capabilities to the FastAPI server by modifying `app/api/main.py`:

```python
from fastapi.staticfiles import StaticFiles
import os

# Define paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CSV_VIEWER_DIR = os.path.join(BASE_DIR, 'app', 'csv_viewer')

# Mount static files directory
app.mount("/static", StaticFiles(directory=CSV_VIEWER_DIR), name="static")
```

### 2. Create CSV Viewer Endpoint

Next, we'll add a new endpoint to serve the CSV viewer HTML file by creating a new router in `app/api/routers/viewer.py`:

```python
"""
CSV Viewer Router

This module provides API endpoints for the CSV viewer.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import logging

from app.api.utils.logging import setup_api_logging

# Create router
router = APIRouter()

# Set up logging
log, _, logger, _ = setup_api_logging()

# Define templates directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
CSV_VIEWER_DIR = os.path.join(BASE_DIR, 'app', 'csv_viewer')

@router.get(
    "/",
    response_class=HTMLResponse,
    summary="CSV Viewer",
    description="Web-based CSV viewer for displaying and analyzing CSV files."
)
async def csv_viewer(request: Request):
    """
    Serve the CSV viewer HTML file.
    
    Args:
        request (Request): The incoming request
        
    Returns:
        HTMLResponse: The CSV viewer HTML page
    """
    try:
        log(f"Serving CSV viewer")
        
        # Read the HTML file
        html_path = os.path.join(CSV_VIEWER_DIR, 'index.html')
        
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
    except Exception as e:
        log(f"Error serving CSV viewer: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Error serving CSV viewer: {str(e)}")
```

### 3. Include the New Router in main.py

Update `app/api/main.py` to include the new router:

```python
from app.api.routers import scripts, data, viewer

# Include routers
app.include_router(scripts.router, prefix="/api/scripts", tags=["scripts"])
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(viewer.router, prefix="/viewer", tags=["viewer"])
```

### 4. Modify the CSV Viewer HTML File

Update `app/csv_viewer/index.html` to fetch CSV data from the API endpoints:

```html
<!-- File selector section -->
<div class="mb-4 p-3 bg-white rounded shadow-sm">
    <label for="file-selector" class="block text-sm font-medium text-gray-700 mb-2">Select CSV File:</label>
    <select id="file-selector" class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
        <option value="">Select a file...</option>
    </select>
</div>

<!-- JavaScript for loading file list and CSV data -->
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const fileSelector = document.getElementById('file-selector');
        const tableContainer = document.getElementById('table-container');
        const loadingIndicator = document.getElementById('loading');
        const errorMessage = document.getElementById('error-message');
        const fileInfo = document.getElementById('file-info');
        
        // Function to show error
        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.classList.remove('hidden');
            loadingIndicator.classList.add('hidden');
        }
        
        // Function to load file list
        function loadFileList() {
            fetch('/api/data/list/strategies')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to load file list');
                    }
                    return response.json();
                })
                .then(data => {
                    if (!data || !data.files) {
                        throw new Error('Invalid response format');
                    }
                    
                    // Add files to selector
                    data.files.forEach(file => {
                        if (file.path.endsWith('.csv')) {
                            const option = document.createElement('option');
                            option.value = file.path;
                            option.textContent = file.path.split('/').pop();
                            fileSelector.appendChild(option);
                        }
                    });
                })
                .catch(error => {
                    showError('Error loading file list: ' + error.message);
                });
        }
        
        // Function to load CSV data
        function loadCSVData(filePath) {
            loadingIndicator.classList.remove('hidden');
            tableContainer.classList.add('hidden');
            errorMessage.classList.add('hidden');
            
            fetch(`/api/data/csv/${filePath}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to load CSV file');
                    }
                    return response.json();
                })
                .then(response => {
                    // Hide loading indicator
                    loadingIndicator.classList.add('hidden');
                    
                    if (!response || !response.data || !response.data.data) {
                        showError('Invalid response format');
                        return;
                    }
                    
                    const data = response.data.data;
                    
                    if (data.length === 0) {
                        showError('No data found in the CSV file.');
                        return;
                    }
                    
                    // Display file info
                    fileInfo.innerHTML = `
                        <p><strong>File:</strong> ${filePath.split('/').pop()}</p>
                        <p><strong>Rows:</strong> ${data.length}</p>
                        <p><strong>Columns:</strong> ${Object.keys(data[0]).length}</p>
                    `;
                    
                    // Show table container
                    tableContainer.classList.remove('hidden');
                    
                    // Initialize DataTable
                    $('#csv-table').DataTable({
                        destroy: true, // Destroy existing table
                        data: data,
                        columns: Object.keys(data[0]).map(key => ({
                            title: key,
                            data: key
                        })),
                        scrollX: true,
                        scrollY: '70vh',
                        scrollCollapse: true,
                        paging: true,
                        searching: true,
                        ordering: true,
                        info: true,
                        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
                        pageLength: 25,
                        responsive: true
                    });
                })
                .catch(error => {
                    showError('Error loading CSV file: ' + error.message);
                });
        }
        
        // Event listener for file selector
        fileSelector.addEventListener('change', function() {
            if (this.value) {
                loadCSVData(this.value);
            }
        });
        
        // Load file list on page load
        loadFileList();
    });
</script>
```

### 5. Update run.py to Enable Hot Reloading

Modify `app/api/run.py` to ensure hot reloading is enabled:

```python
def main():
    """Run the API server."""
    parser = argparse.ArgumentParser(description="Run the API server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", default=True, help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    config = get_config()
    os.makedirs(config["LOG_DIR"], exist_ok=True)
    
    print(f"Starting API server at http://{args.host}:{args.port}")
    print(f"API documentation available at http://{args.host}:{args.port}/docs")
    print(f"CSV Viewer available at http://{args.host}:{args.port}/viewer")
    
    # Run the server
    uvicorn.run(
        "app.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level
    )
```

### 6. Create a README for the CSV Viewer

Create `app/csv_viewer/README.md` to document the CSV viewer:

```markdown
# CSV Viewer

A web-based CSV viewer for displaying and analyzing CSV files.

## Features

- View CSV files in a tabular format
- Sort, filter, and paginate data
- Responsive design
- Support for large CSV files

## Accessing the CSV Viewer

The CSV viewer is integrated with the API server and can be accessed at:

```
http://127.0.0.1:8000/viewer
```

## Usage

1. Select a CSV file from the dropdown menu
2. The file will be loaded and displayed in the table
3. Use the search box to filter data
4. Click on column headers to sort
5. Use the pagination controls to navigate through large datasets

## Development

The CSV viewer is served by the FastAPI server with hot reloading enabled. Any changes to the HTML file will be automatically reflected in the browser.

To run the server with hot reloading:

```
python -m app.api.run --reload
```
```

## Implementation Benefits

This implementation offers several advantages:

1. **Hot Reloading**: Changes to the HTML file will be automatically reflected in the browser
2. **Integration**: Seamless integration with the existing API server
3. **Performance**: High performance with Uvicorn's asynchronous request handling
4. **API Access**: Direct access to the API endpoints for fetching CSV data
5. **Maintainability**: Single server to maintain

## Testing the Implementation

1. Start the server with hot reloading:
   ```
   python -m app.api.run --reload
   ```

2. Access the CSV viewer at:
   ```
   http://127.0.0.1:8000/viewer
   ```

3. Test loading different CSV files from the dropdown menu

4. Make changes to the HTML file and verify that they are automatically reflected in the browser
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

## Implementation Details

The CSV viewer is implemented as an extension to the existing FastAPI server. It uses the following components:

1. **FastAPI Router**: A dedicated router for serving the CSV viewer HTML file
2. **Static File Serving**: For serving static assets like CSS and JavaScript
3. **API Integration**: Uses the existing API endpoints to fetch CSV data
4. **Hot Reloading**: Changes to the HTML file are automatically reflected in the browser

## Technical Stack

- **Backend**: FastAPI with Uvicorn
- **Frontend**: HTML, JavaScript, TailwindCSS
- **Data Processing**: PapaParse for CSV parsing
- **Data Display**: DataTables for tabular display with sorting and filtering

## Troubleshooting

If you encounter issues with the CSV viewer, check the following:

1. Ensure the API server is running
2. Check the browser console for JavaScript errors
3. Verify that the CSV files are accessible in the `csv/` directory
4. Check the API server logs for any backend errors

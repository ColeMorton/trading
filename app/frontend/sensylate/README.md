# Sensylate

Sensitivity analysis meets portfolio simulation and strategy creation.

## Implementation Details

This application has been implemented using the following technologies:

- **Frontend**: HTML, JavaScript, CSS
- **Build Tools**: Webpack for bundling
- **Backend**: FastAPI with Uvicorn
- **Data Processing**: PapaParse for CSV parsing
- **Data Display**: DataTables for tabular display with sorting and filtering

## Features

- View CSV files in a tabular format
- Sort, filter, and paginate data
- Responsive design
- Support for large CSV files
- Portfolio update functionality

## Accessing Sensylate

Sensylate is integrated with the API server and can be accessed at:

```
http://127.0.0.1:8000/viewer
```

## Usage

1. Select a CSV file from the dropdown menu
2. The file will be loaded and displayed in the table
3. Use the search box to filter data
4. Click on column headers to sort
5. Use the pagination controls to navigate through large datasets
6. Use the "Update" button to refresh portfolio data

## Development

### Setup

Sensylate uses Webpack for bundling and Tailwind CSS for styling. To set up the development environment:

1. Install dependencies:

   ```
   cd app/sensylate
   npm install
   ```

2. Start the Webpack development server:

   ```
   npm run start
   ```

3. In a separate terminal, run the FastAPI server:
   ```
   python -m app.api.run --reload
   ```

### Development and Production Modes

The application supports both development and production modes:

#### Development Mode

For development, you can run the application using:

```bash
cd app/sensylate
npm run start
```

This will start the Webpack development server with hot reloading.

#### Production Mode

For production, you can build the application using:

```bash
cd app/sensylate
npm run build
```

This will create optimized assets in the `dist` directory, which will be served by the FastAPI server.
In the future, a production build process will be implemented to create optimized assets in the `dist` directory.

## Implementation Details

Sensylate is implemented as an extension to the existing FastAPI server. It uses the following components:

1. **FastAPI Router**: A dedicated router for serving the Sensylate HTML file
2. **Static File Serving**: For serving static assets like CSS and JavaScript
3. **API Integration**: Uses the existing API endpoints to fetch CSV data
4. **Webpack**: For bundling JavaScript, CSS, and other assets
5. **Tailwind CSS**: For utility-first styling

## Technical Stack

- **Backend**: FastAPI with Uvicorn
- **Frontend**: HTML, JavaScript, Tailwind CSS
- **Build Tools**: Webpack, PostCSS
- **Data Processing**: PapaParse for CSV parsing
- **Data Display**: DataTables for tabular display with sorting and filtering

## Project Structure

```
app/sensylate/
├── dist/               # Compiled assets (created by Webpack)
├── src/                # Source files
│   ├── index.html      # Main HTML file
│   ├── scripts/        # JavaScript files
│   │   └── main.js     # Main JavaScript entry point
│   └── styles/         # CSS files
│       └── main.css    # Main CSS file with Tailwind imports
├── node_modules/       # Node.js dependencies
├── package.json        # Node.js package configuration
├── webpack.config.js   # Webpack configuration
├── postcss.config.js   # PostCSS configuration
├── tailwind.config.js  # Tailwind CSS configuration
└── README.md           # This documentation
```

## Troubleshooting

If you encounter issues with Sensylate, check the following:

1. Ensure the API server is running
2. Check the browser console for JavaScript errors
3. Verify that the CSV files are accessible in the `csv/` directory
4. Check the API server logs for any backend errors
5. Ensure all Node.js dependencies are installed
6. Check Webpack build errors in the console

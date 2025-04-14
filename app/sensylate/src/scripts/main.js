// Import styles
import '../styles/main.css';

// Import dependencies
import $ from 'jquery';
import 'datatables.net';
// Import DataTables CSS directly in the HTML file for now
import Papa from 'papaparse';

document.addEventListener('DOMContentLoaded', function() {
    const fileSelector = document.getElementById('file-selector');
    const tableContainer = document.getElementById('table-container');
    const textContainer = document.getElementById('text-container');
    const loadingIndicator = document.getElementById('loading');
    const errorMessage = document.getElementById('error-message');
    const fileInfo = document.getElementById('file-info');
    const tableViewBtn = document.getElementById('table-view-btn');
    const textViewBtn = document.getElementById('text-view-btn');
    const csvText = document.getElementById('csv-text');
    
    // Function to switch to table view
    function showTableView() {
        tableContainer.classList.remove('hidden');
        textContainer.classList.add('hidden');
        tableViewBtn.classList.remove('bg-gray-200', 'text-gray-700');
        tableViewBtn.classList.add('bg-indigo-600', 'text-white');
        textViewBtn.classList.remove('bg-indigo-600', 'text-white');
        textViewBtn.classList.add('bg-gray-200', 'text-gray-700');
    }
    
    // Function to switch to text view
    function showTextView() {
        tableContainer.classList.add('hidden');
        textContainer.classList.remove('hidden');
        tableViewBtn.classList.remove('bg-indigo-600', 'text-white');
        tableViewBtn.classList.add('bg-gray-200', 'text-gray-700');
        textViewBtn.classList.remove('bg-gray-200', 'text-gray-700');
        textViewBtn.classList.add('bg-indigo-600', 'text-white');
    }
    
    // Event listeners for toggle buttons
    tableViewBtn.addEventListener('click', showTableView);
    textViewBtn.addEventListener('click', showTextView);
    
    // Function to convert CSV data to raw text using PapaParse
    function convertToRawText(data, columns) {
        // Use PapaParse to convert JSON data back to CSV
        try {
            return Papa.unparse(data);
        } catch (error) {
            console.error("Error using Papa.unparse:", error);
            
            // Fallback to manual conversion if PapaParse fails
            // Create header row
            let rawText = columns.join(',') + '\n';
            
            // Add data rows
            data.forEach(row => {
                const rowValues = columns.map(col => {
                    // Get the value and handle null/undefined
                    let value = row[col];
                    
                    // Format numbers appropriately for CSV
                    if (typeof value === 'number') {
                        // Don't round numbers in the raw CSV data
                        value = String(value);
                    } else {
                        // Handle null/undefined
                        value = value !== null && value !== undefined ? String(value) : '';
                    }
                    
                    // Handle values with commas by quoting them
                    return value.includes(',') ? `"${value}"` : value;
                });
                rawText += rowValues.join(',') + '\n';
            });
            
            return rawText;
        }
    }
    
    // Function to show error
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
        loadingIndicator.classList.add('hidden');
    }
    
    // Function to load file list
    function loadFileList() {
        loadingIndicator.classList.remove('hidden');
        
        fetch('/api/data/list/strategies')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load file list');
                }
                return response.json();
            })
            .then(data => {
                loadingIndicator.classList.add('hidden');
                
                if (!data || !data.files) {
                    throw new Error('Invalid response format');
                }
                
                // Filter for CSV files only
                const csvFiles = data.files.filter(file => file.path.endsWith('.csv'));
                
                // Sort files by filename (not the full path)
                csvFiles.sort((a, b) => {
                    const filenameA = a.path.split('/').pop();
                    const filenameB = b.path.split('/').pop();
                    return filenameA.localeCompare(filenameB);
                });
                
                // Add sorted files to selector
                csvFiles.forEach(file => {
                    const option = document.createElement('option');
                    option.value = file.path;
                    option.textContent = file.path.split('/').pop();
                    fileSelector.appendChild(option);
                });
            })
            .catch(error => {
                showError('Error loading file list: ' + error.message);
            });
    }
    
    // Function to parse CSV data using PapaParse
    function parseCSVWithPapa(csvText) {
        return new Promise((resolve, reject) => {
            if (!csvText || typeof csvText !== 'string' || csvText.trim() === '') {
                console.error("Invalid CSV text provided to parseCSVWithPapa:", csvText);
                reject(new Error("Invalid or empty CSV text"));
                return;
            }

            console.log("CSV text sample (first 100 chars):", csvText.substring(0, 100));
            
            Papa.parse(csvText, {
                header: true,  // This tells PapaParse to use the first row as headers
                dynamicTyping: true,
                skipEmptyLines: true,
                complete: function(results) {
                    console.log("PapaParse successfully parsed CSV data:", results.meta);
                    
                    if (results.errors && results.errors.length > 0) {
                        console.warn("PapaParse encountered non-fatal errors:", results.errors);
                    }
                    
                    if (!results.data || results.data.length === 0) {
                        console.warn("PapaParse returned empty data set");
                    } else {
                        console.log(`PapaParse parsed ${results.data.length} rows of data`);
                        console.log("First row sample:", results.data[0]);
                    }
                    
                    // Store the original headers from the CSV
                    const headers = results.meta.fields;
                    console.log("CSV Headers:", headers);
                    
                    // Return both the data and headers
                    resolve({
                        data: results.data,
                        headers: headers
                    });
                },
                error: function(error) {
                    console.error("PapaParse error:", error);
                    reject(error);
                }
            });
        });
    }
    
    // Function to load CSV data
    function loadCSVData(filePath) {
        console.log(`Loading CSV data for file: ${filePath}`);
        loadingIndicator.classList.remove('hidden');
        tableContainer.classList.add('hidden');
        textContainer.classList.add('hidden');
        errorMessage.classList.add('hidden');
        document.getElementById('view-toggle').classList.add('hidden');
        
        // Directly use the JSON API since we know the server returns JSON
        console.log(`Fetching CSV data as JSON: /api/data/csv/${filePath}`);
        fetch(`/api/data/csv/${filePath}`)
            .then(response => {
                if (!response.ok) {
                    console.error(`JSON API fetch failed with status: ${response.status}`);
                    throw new Error(`Failed to load CSV file: ${response.statusText}`);
                }
                return response.json();
            })
            .then(jsonData => {
                console.log("Received JSON data from API:", jsonData ? Object.keys(jsonData) : 'null');
                return { type: 'json', data: jsonData };
            })
            .then(result => {
                // Hide loading indicator
                loadingIndicator.classList.add('hidden');
                
                // Properly handle different response formats
                const response = result.data;
                
                if (!response || !response.data) {
                    console.error("Invalid response format:", response);
                    showError('Invalid response format');
                    return;
                }
                
                // Ensure we're accessing the correct data structure
                let data;
                if (response.data && response.data.data && Array.isArray(response.data.data)) {
                    // Standard API response format
                    data = response.data.data;
                } else if (Array.isArray(response.data)) {
                    // Direct data array
                    data = response.data;
                } else {
                    console.error("Unexpected data format:", response);
                    showError('Invalid data format received from server');
                    return;
                }
                
                if (!data || data.length === 0) {
                    console.error("Empty data array in CSV file");
                    showError('No data found in the CSV file. The file may be empty or have an invalid format.');
                    return;
                }
                
                console.log("Parsed data sample:", data.slice(0, 3));
                
                // Debug: Check for Win Rate [%] column and its values
                console.log("All columns:", Object.keys(data[0]));
                const winRateKey = Object.keys(data[0]).find(key =>
                    key.includes("Win Rate") || key.includes("Win_Rate"));
                
                if (winRateKey) {
                    console.log(`Found Win Rate column: "${winRateKey}"`);
                    console.log("First few Win Rate values:",
                        data.slice(0, 5).map(row => ({
                            value: row[winRateKey],
                            type: typeof row[winRateKey]
                        }))
                    );
                } else {
                    console.log("No Win Rate column found in data");
                }
                
                // Display file info
                fileInfo.innerHTML = `
                    <p><strong>File:</strong> ${filePath.split('/').pop()}</p>
                    <p><strong>Rows:</strong> ${data.length}</p>
                    <p><strong>Columns:</strong> ${Object.keys(data[0]).length}</p>
                `;
                
                // Show view toggle buttons
                document.getElementById('view-toggle').classList.remove('hidden');
                
                // Get columns
                const columns = Object.keys(data[0]);
                // Populate raw text view with original data (not the cleaned version)
                // If we parsed the CSV ourselves, we should also set the raw text
                if (result.type === 'csv') {
                    try {
                        // Get the original CSV text
                        const originalText = Papa.unparse(data);
                        csvText.value = originalText;
                    } catch (error) {
                        console.error("Error using Papa.unparse for raw data:", error);
                        // Fallback to convertToRawText
                        const rawText = convertToRawText(data, columns);
                        csvText.value = rawText;
                    }
                } else {
                    // Use the convertToRawText function for JSON data
                    const rawText = convertToRawText(data, columns);
                    csvText.value = rawText;
                }
                
                
                // Show table view by default
                showTableView();
                
                // Find the index of the "Score" column
                const scoreColumnIndex = columns.findIndex(col => col === "Score");
                
                // Log the data to help debug
                console.log("CSV Data Sample:", data.slice(0, 3));
                
                // Check for Win Rate column
                const winRateColumn = columns.find(col => col.includes("Win Rate") || col.includes("Win_Rate"));
                if (winRateColumn) {
                    console.log(`Win Rate column found: "${winRateColumn}"`);
                    console.log("Sample Win Rate values:", data.slice(0, 3).map(row => row[winRateColumn]));
                } else {
                    console.log("No Win Rate column found in:", columns);
                }
                
                // Create a clean version of the data for DataTables
                // This addresses issues with columns containing special characters like [%]
                const cleanData = data.map(row => {
                    const cleanRow = {};
                    Object.keys(row).forEach(key => {
                        // Create a clean key without special characters for internal use
                        const cleanKey = key.replace(/[\[\]%]/g, '_');
                        cleanRow[cleanKey] = row[key];
                    });
                    return cleanRow;
                });
                
                // Create a mapping between original column names and clean column names
                const columnMapping = {};
                columns.forEach(key => {
                    const cleanKey = key.replace(/[\[\]%]/g, '_');
                    columnMapping[cleanKey] = key;
                });
                
                // Log the column mapping for debugging
                console.log("Column mapping:", columnMapping);
                
                // Get clean column names
                const cleanColumns = Object.keys(cleanData[0]);
                
                // Clear any existing DataTable
                if ($.fn.DataTable.isDataTable('#csv-table')) {
                    $('#csv-table').DataTable().destroy();
                    $('#csv-table').empty();
                }
                
                // Initialize DataTable with simple configuration (similar to the working version)
                $('#csv-table').DataTable({
                    data: cleanData,
                    columns: cleanColumns.map(cleanKey => {
                        const originalKey = columnMapping[cleanKey];
                        return {
                            title: originalKey,
                            data: cleanKey,
                            render: function(data, type, row) {
                                // For sorting and type detection
                                if (type === 'sort' || type === 'type') {
                                    return data === null || data === undefined ? '' : data;
                                }
                                
                                // For display
                                if (data === null || data === undefined) {
                                    return '';
                                }
                                
                                // Special handling for percentage columns
                                if (originalKey.includes('[%]') ||
                                    originalKey.toLowerCase().includes('rate') ||
                                    originalKey.toLowerCase().includes('percent')) {
                                    if (typeof data === 'number') {
                                        return data.toFixed(2) + '%';
                                    } else if (typeof data === 'string' && !isNaN(parseFloat(data))) {
                                        return (parseFloat(data)).toFixed(2) + '%';
                                    }
                                }
                                
                                // Format numbers with appropriate precision
                                if (typeof data === 'number') {
                                    if (data === 0) return '0';
                                    else if (Math.abs(data) < 0.01) return data.toExponential(4);
                                    else if (Math.abs(data) >= 1000) return data.toLocaleString(undefined, {maximumFractionDigits: 2});
                                    else return data.toLocaleString(undefined, {maximumFractionDigits: 4});
                                }
                                
                                return data;
                            }
                        };
                    }),
                    scrollX: true,
                    scrollY: '70vh',
                    scrollCollapse: true,
                    paging: false,
                    searching: true,
                    ordering: true,
                    info: true,
                    lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
                    pageLength: "All",
                    order: scoreColumnIndex !== -1 ? [[scoreColumnIndex, 'desc']] : []
                });
            })
            .catch(error => {
                console.error("Error in loadCSVData:", error);
                
                // Try one more approach - direct file fetch and parse with PapaParse
                if (filePath.startsWith('http') || filePath.includes('/')) {
                    console.log("Attempting direct CSV parsing with PapaParse");
                    // This is a URL or path, try to fetch it directly
                    Papa.parse(filePath, {
                        download: true,
                        header: true,
                        dynamicTyping: true,
                        skipEmptyLines: true,
                        complete: function(results) {
                            console.log("PapaParse direct parsing results:", results);
                            if (results.data && results.data.length > 0) {
                                console.log("Successfully parsed CSV directly with PapaParse");
                                
                                // Process the data similar to the main flow
                                const data = results.data;
                                
                                // Hide loading indicator
                                loadingIndicator.classList.add('hidden');
                                
                                // Display file info
                                fileInfo.innerHTML = `
                                    <p><strong>File:</strong> ${filePath.split('/').pop()}</p>
                                    <p><strong>Rows:</strong> ${data.length}</p>
                                    <p><strong>Columns:</strong> ${Object.keys(data[0]).length}</p>
                                    <p><em>Parsed directly with PapaParse</em></p>
                                `;
                                
                                // Show view toggle buttons
                                document.getElementById('view-toggle').classList.remove('hidden');
                                
                                // Get columns
                                const columns = Object.keys(data[0]);
                                
                                // Set raw text
                                csvText.value = Papa.unparse(data);
                                
                                // Show table view by default
                                showTableView();
                                
                                // Clear any existing DataTable
                                if ($.fn.DataTable.isDataTable('#csv-table')) {
                                    $('#csv-table').DataTable().destroy();
                                    $('#csv-table').empty();
                                }
                                
                                // Initialize DataTable with simple configuration
                                $('#csv-table').DataTable({
                                    data: data,
                                    columns: columns.map(col => ({
                                        title: col,
                                        data: col,
                                        render: function(data, type, row) {
                                            // For sorting and type detection
                                            if (type === 'sort' || type === 'type') {
                                                return data === null || data === undefined ? '' : data;
                                            }
                                            
                                            // For display
                                            if (data === null || data === undefined) {
                                                return '';
                                            }
                                            
                                            // Format numbers with appropriate precision
                                            if (typeof data === 'number') {
                                                if (data === 0) return '0';
                                                else if (Math.abs(data) < 0.01) return data.toExponential(4);
                                                else if (Math.abs(data) >= 1000) return data.toLocaleString(undefined, {maximumFractionDigits: 2});
                                                else return data.toLocaleString(undefined, {maximumFractionDigits: 4});
                                            }
                                            
                                            return data;
                                        }
                                    })),
                                    scrollX: true,
                                    scrollY: '70vh',
                                    scrollCollapse: true,
                                    paging: false,
                                    searching: true,
                                    ordering: true,
                                    info: true
                                });
                            } else {
                                console.error("PapaParse direct parsing: No data found");
                                showError('Error parsing CSV file directly: No data found. The file may be empty or have an invalid format.');
                            }
                        },
                        error: function(error) {
                            console.error("PapaParse direct parsing error:", error);
                            showError('Error loading CSV file: ' + error.message);
                        }
                    });
                } else {
                    console.error("Error loading CSV file:", error);
                    showError('Error loading CSV file: ' + error.message);
                }
            });
    }
    // Event listener for file selector
    fileSelector.addEventListener('change', function() {
        if (this.value) {
            loadCSVData(this.value);
            
            // Enable Update button when a file is selected
            const updateButton = document.getElementById('update-button');
            updateButton.disabled = false;
        } else {
            // Disable Update button when no file is selected
            const updateButton = document.getElementById('update-button');
            updateButton.disabled = true;
        }
    });
    
    // Add event listener for Update button
    document.getElementById('update-button').addEventListener('click', function() {
        const filePath = fileSelector.value;
        if (!filePath) return;
        
        // Show loading state
        this.disabled = true;
        this.innerHTML = '<span class="animate-spin inline-block mr-2">↻</span> Updating...';
        
        // Hide previous status
        const updateStatus = document.getElementById('update-status');
        updateStatus.classList.add('hidden');
        
        // Get just the filename without the path
        const fileName = filePath.split('/').pop();
        
        // Make API request to update portfolio
        fetch('/api/scripts/update-portfolio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                portfolio: fileName
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Show status message
            updateStatus.classList.remove('hidden');
            
            if (data.status === "accepted") {
                updateStatus.className = 'mb-4 p-3 bg-blue-100 text-blue-800 rounded shadow-sm';
                updateStatus.textContent = `Portfolio update started. Execution ID: ${data.execution_id}`;
                // Store button reference for use in event handlers
                const updateButton = this;
                
                // Create SSE connection
                const executionId = data.execution_id;
                const eventSource = new EventSource(`/api/scripts/status-stream/${executionId}`);
                
                // Handle incoming messages
                eventSource.onmessage = function(event) {
                    try {
                        const statusData = JSON.parse(event.data);
                        
                        // Update status message based on progress
                        if (statusData.status === "completed") {
                            // Update status message
                            updateStatus.className = 'mb-4 p-3 bg-green-100 text-green-800 rounded shadow-sm';
                            updateStatus.textContent = 'Portfolio updated successfully!';
                            
                            // Reset button
                            updateButton.disabled = false;
                            updateButton.textContent = 'Update';
                            
                            // Reload the CSV data to refresh the table
                            loadCSVData(filePath);
                            
                            // Close the connection
                            eventSource.close();
                        } else if (statusData.status === "failed") {
                            // Update status message
                            updateStatus.className = 'mb-4 p-3 bg-red-100 text-red-800 rounded shadow-sm';
                            updateStatus.textContent = `Update failed: ${statusData.error || 'Unknown error'}`;
                            
                            // Reset button
                            updateButton.disabled = false;
                            updateButton.textContent = 'Update';
                            
                            // Close the connection
                            eventSource.close();
                        } else {
                            // Update progress message
                            const progressText = statusData.progress ? `(${statusData.progress}%)` : '';
                            updateStatus.textContent = `Portfolio update in progress... Status: ${statusData.status} ${progressText}`;
                            
                            // Add progress bar if not already present
                            if (!document.getElementById('progress-bar-container')) {
                                const progressContainer = document.createElement('div');
                                progressContainer.id = 'progress-bar-container';
                                progressContainer.className = 'w-full bg-gray-200 rounded-full h-2.5 mt-2';
                                
                                const progressBar = document.createElement('div');
                                progressBar.id = 'progress-bar';
                                progressBar.className = 'bg-indigo-600 h-2.5 rounded-full';
                                progressBar.style.width = `${statusData.progress || 0}%`;
                                
                                progressContainer.appendChild(progressBar);
                                updateStatus.appendChild(progressContainer);
                            } else {
                                // Update existing progress bar
                                const progressBar = document.getElementById('progress-bar');
                                if (progressBar) {
                                    progressBar.style.width = `${statusData.progress || 0}%`;
                                }
                            }
                        }
                    } catch (error) {
                        console.error('Error parsing SSE message:', error);
                    }
                };
                
                // Handle connection errors
                eventSource.onerror = function(error) {
                    console.error('SSE connection error:', error);
                    
                    // Update status message
                    updateStatus.className = 'mb-4 p-3 bg-red-100 text-red-800 rounded shadow-sm';
                    updateStatus.textContent = `Error checking status: Connection lost`;
                    
                    // Reset button
                    updateButton.disabled = false;
                    updateButton.textContent = 'Update';
                    
                    // Close the connection
                    eventSource.close();
                };
            } else {
                updateStatus.className = 'mb-4 p-3 bg-red-100 text-red-800 rounded shadow-sm';
                updateStatus.textContent = `Error: ${data.message || 'Unknown error'}`;
                
                // Reset button
                this.disabled = false;
                this.textContent = 'Update';
            }
        })
        .catch(error => {
            // Reset button
            this.disabled = false;
            this.textContent = 'Update';
            
            // Show error message
            updateStatus.classList.remove('hidden');
            updateStatus.className = 'mb-4 p-3 bg-red-100 text-red-800 rounded shadow-sm';
            updateStatus.textContent = `Error starting update: ${error.message}`;
        });
    });
    
    // Load file list on page load
    loadFileList();
});
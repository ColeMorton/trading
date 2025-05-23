/**
 * Analysis module for handling parameter sensitivity analysis.
 */
const Analysis = (function() {
    // Private variables
    let resultsData = [];
    let csvFiles = [];
    let currentCsvFile = null;
    
    /**
     * Initialize the analysis module.
     */
    function init() {
        // Set up event listeners
        const runAnalysisBtn = document.getElementById('run-analysis-btn');
        if (runAnalysisBtn) {
            runAnalysisBtn.addEventListener('click', runAnalysis);
        } else {
            console.error('Run analysis button not found in the DOM');
        }
        
        // Set up CSV file selector dropdown
        const csvSelector = document.getElementById('csv-file-selector');
        if (csvSelector) {
            csvSelector.addEventListener('change', function() {
                const selectedValue = this.value;
                if (selectedValue) {
                    loadCsvFile(selectedValue);
                }
            });
        }
        
        // Set up download button
        const downloadBtn = document.getElementById('download-csv-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', downloadCurrentCsv);
        }
    }
    
    /**
     * Run the analysis with the current configuration.
     */
    function runAnalysis() {
        // Get the tickers
        const tickersInput = document.getElementById('tickers-input');
        if (!tickersInput) {
            console.error('Tickers input not found');
            return;
        }
        
        const tickers = tickersInput.value.trim();
        if (!tickers) {
            showError('Please enter at least one ticker');
            return;
        }
        
        // Get the configuration
        const config = getConfiguration();
        
        // Show loading indicator
        showLoading(true);
        
        // Send the request to the server
        fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tickers: tickers,
                config: config
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading indicator
            showLoading(false);
            
            if (data.status === 'success') {
                // Store the results
                resultsData = data.results || [];
                
                // Store CSV files
                csvFiles = data.csv_files || [];
                
                // Update CSV file selector
                updateCsvFileSelector();
                
                // Display the results
                displayResults();
                
                // Show success message
                showSuccess(data.message || 'Analysis completed successfully');
            } else {
                // Show error message
                showError(data.message || 'Analysis failed');
            }
        })
        .catch(error => {
            // Hide loading indicator
            showLoading(false);
            
            // Show error message
            showError('An error occurred: ' + error.message);
        });
    }
    
    /**
     * Get the current configuration from the form.
     */
    function getConfiguration() {
        // Helper function to safely get element value
        function getElementValue(id, defaultValue) {
            const element = document.getElementById(id);
            return element ? element.value : defaultValue;
        }
        
        // Helper function to safely get checkbox state
        function getCheckboxState(id, defaultState) {
            const element = document.getElementById(id);
            return element ? element.checked : defaultState;
        }
        
        return {
            WINDOWS: parseInt(getElementValue('windows-input', '89')) || 89,
            REFRESH: getCheckboxState('refresh-checkbox', true),
            STRATEGY_TYPES: getSelectedStrategyTypes(),
            DIRECTION: getElementValue('direction-select', 'Long'),
            USE_HOURLY: getCheckboxState('use-hourly-checkbox', false),
            USE_YEARS: getCheckboxState('use-years-checkbox', false),
            YEARS: parseInt(getElementValue('years-input', '15')) || 15,
            USE_SYNTHETIC: getCheckboxState('use-synthetic-checkbox', false),
            USE_CURRENT: getCheckboxState('use-current-checkbox', true),
            MINIMUMS: {
                WIN_RATE: parseFloat(getElementValue('min-win-rate-input', '0.44')) || 0.44,
                TRADES: parseInt(getElementValue('min-trades-input', '54')) || 54,
                EXPECTANCY_PER_TRADE: parseFloat(getElementValue('min-expectancy-input', '1')) || 1,
                PROFIT_FACTOR: parseFloat(getElementValue('min-profit-factor-input', '1')) || 1,
                SORTINO_RATIO: parseFloat(getElementValue('min-sortino-input', '0.4')) || 0.4
            },
            SORT_BY: getElementValue('sort-by-select', 'Score'),
            SORT_ASC: getCheckboxState('sort-asc-checkbox', false),
            USE_GBM: getCheckboxState('use-gbm-checkbox', false)
        };
    }
    
    /**
     * Get the selected strategy types.
     */
    function getSelectedStrategyTypes() {
        const strategyTypes = [];
        
        const smaCheckbox = document.getElementById('sma-checkbox');
        if (smaCheckbox && smaCheckbox.checked) {
            strategyTypes.push('SMA');
        }
        
        const emaCheckbox = document.getElementById('ema-checkbox');
        if (emaCheckbox && emaCheckbox.checked) {
            strategyTypes.push('EMA');
        }
        
        return strategyTypes.length > 0 ? strategyTypes : ['SMA', 'EMA'];
    }
    
    /**
     * Update the CSV file selector dropdown with available files.
     */
    function updateCsvFileSelector() {
        const selector = document.getElementById('csv-file-selector');
        if (!selector) return;
        
        // Clear existing options
        selector.innerHTML = '';
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select a CSV file...';
        selector.appendChild(defaultOption);
        
        // Add option for current results
        const currentOption = document.createElement('option');
        currentOption.value = 'current';
        currentOption.textContent = 'Current Results';
        currentOption.selected = true;
        selector.appendChild(currentOption);
        
        // Group files by type
        const bestFiles = csvFiles.filter(file => file.type === 'best');
        const filteredFiles = csvFiles.filter(file => file.type === 'filtered');
        
        // Add best files group
        if (bestFiles.length > 0) {
            const bestGroup = document.createElement('optgroup');
            bestGroup.label = 'Best Portfolios';
            
            bestFiles.forEach(file => {
                const option = document.createElement('option');
                option.value = file.file_name;
                option.textContent = file.display_name;
                bestGroup.appendChild(option);
            });
            
            selector.appendChild(bestGroup);
        }
        
        // Add filtered files group
        if (filteredFiles.length > 0) {
            const filteredGroup = document.createElement('optgroup');
            filteredGroup.label = 'Filtered Portfolios';
            
            filteredFiles.forEach(file => {
                const option = document.createElement('option');
                option.value = file.file_name;
                option.textContent = file.display_name;
                filteredGroup.appendChild(option);
            });
            
            selector.appendChild(filteredGroup);
        }
        
        // Enable the selector if we have files
        selector.disabled = csvFiles.length === 0;
        
        // Show the selector container
        const selectorContainer = document.getElementById('csv-selector-container');
        if (selectorContainer) {
            selectorContainer.style.display = csvFiles.length > 0 ? 'block' : 'none';
        }
        
        // Show download button
        const downloadBtn = document.getElementById('download-csv-btn');
        if (downloadBtn) {
            downloadBtn.style.display = csvFiles.length > 0 ? 'inline-block' : 'none';
        }
    }
    
    /**
     * Load a CSV file and display its contents.
     */
    function loadCsvFile(fileName) {
        // If 'current' is selected, display the current results
        if (fileName === 'current') {
            displayResults(resultsData);
            return;
        }
        
        // Find the file in the csvFiles array
        const fileInfo = csvFiles.find(file => file.file_name === fileName);
        if (!fileInfo) {
            showError('File not found');
            return;
        }
        
        // Show loading indicator
        showLoading(true);
        
        // Determine the file path
        const filePath = fileInfo.type === 'best'
            ? `portfolios_best/${fileName}`
            : `portfolios_filtered/${fileName}`;
        
        // Fetch the CSV file
        fetch(`/api/csv/${filePath}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load CSV file');
                }
                return response.text();
            })
            .then(csvText => {
                // Parse CSV text to array of objects
                const parsedData = parseCSV(csvText);
                
                // Store the current CSV file
                currentCsvFile = {
                    fileName: fileName,
                    fileInfo: fileInfo,
                    data: parsedData
                };
                
                // Display the results
                displayResults(parsedData);
                
                // Hide loading indicator
                showLoading(false);
            })
            .catch(error => {
                // Hide loading indicator
                showLoading(false);
                
                // Show error message
                showError('Error loading CSV file: ' + error.message);
            });
    }
    
    /**
     * Parse CSV text to array of objects.
     */
    function parseCSV(csvText) {
        // Split by lines
        const lines = csvText.split('\n');
        
        // Get headers
        const headers = lines[0].split(',');
        
        // Parse data rows
        const data = [];
        for (let i = 1; i < lines.length; i++) {
            if (lines[i].trim() === '') continue;
            
            const values = lines[i].split(',');
            const row = {};
            
            for (let j = 0; j < headers.length; j++) {
                row[headers[j]] = values[j];
            }
            
            data.push(row);
        }
        
        return data;
    }
    
    /**
     * Download the currently displayed CSV file.
     */
    function downloadCurrentCsv() {
        // If no CSV file is selected, use the current results
        if (!currentCsvFile) {
            // Convert current results to CSV
            const csv = convertToCSV(resultsData);
            
            // Create a download link
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'analysis_results.csv';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            return;
        }
        
        // Get file info
        const fileInfo = currentCsvFile.fileInfo;
        
        // Determine the file path
        const filePath = fileInfo.type === 'best'
            ? `portfolios_best/${fileInfo.fileName}`
            : `portfolios_filtered/${fileInfo.fileName}`;
        
        // Create a download link
        const a = document.createElement('a');
        a.href = `/api/csv/${filePath}`;
        a.download = fileInfo.fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
    
    /**
     * Convert an array of objects to CSV string.
     */
    function convertToCSV(data) {
        if (!data || data.length === 0) return '';
        
        // Get headers
        const headers = Object.keys(data[0]);
        
        // Create header row
        let csv = headers.join(',') + '\n';
        
        // Add data rows
        data.forEach(row => {
            const values = headers.map(header => {
                const value = row[header];
                // Handle values with commas by wrapping in quotes
                return typeof value === 'string' && value.includes(',')
                    ? `"${value}"`
                    : value;
            });
            csv += values.join(',') + '\n';
        });
        
        return csv;
    }
    
    /**
     * Display the results in the results container.
     */
    function displayResults(data = null) {
        const resultsContainer = document.getElementById('results-container');
        const resultsTable = document.getElementById('results-table');
        
        if (!resultsContainer || !resultsTable) {
            console.error('Results container or table not found');
            return;
        }
        
        // Use provided data or fall back to resultsData
        const displayData = data || resultsData;
        
        if (!displayData || displayData.length === 0) {
            resultsContainer.innerHTML = '<p class="text-center">No results available</p>';
            return;
        }
        
        // Get the table headers from the first result
        const headers = Object.keys(displayData[0]);
        
        // Create the table header
        let tableHtml = '<thead><tr>';
        headers.forEach(header => {
            tableHtml += `<th>${header}</th>`;
        });
        tableHtml += '<th>Actions</th></tr></thead>';
        
        // Create the table body
        tableHtml += '<tbody>';
        displayData.forEach(result => {
            tableHtml += '<tr>';
            headers.forEach(header => {
                tableHtml += `<td>${formatValue(result[header], header)}</td>`;
            });
            tableHtml += `<td><button class="btn btn-sm btn-primary add-to-portfolio-btn" data-index="${displayData.indexOf(result)}">Add to Portfolio</button></td>`;
            tableHtml += '</tr>';
        });
        tableHtml += '</tbody>';
        
        // Update the table
        resultsTable.innerHTML = tableHtml;
        
        // Add event listeners to the Add to Portfolio buttons
        document.querySelectorAll('.add-to-portfolio-btn').forEach(button => {
            button.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                addToPortfolio(displayData[index]);
            });
        });
        
        // Show the results container
        resultsContainer.style.display = 'block';
    }
    
    /**
     * Format a value for display.
     */
    function formatValue(value, header) {
        if (value === undefined || value === null) {
            return '';
        }
        
        if (typeof value === 'number') {
            if (header.includes('[%]') || header.includes('Rate') || header.includes('Percent')) {
                return value.toFixed(2) + '%';
            } else if (Math.abs(value) < 0.01) {
                return value.toFixed(4);
            } else if (Math.abs(value) >= 1000) {
                return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
            } else {
                return value.toFixed(4);
            }
        }
        
        return value;
    }
    
    /**
     * Add a result to the portfolio.
     */
    function addToPortfolio(result) {
        fetch('/api/portfolio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(result)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showSuccess('Added to portfolio');
            } else {
                showError(data.message || 'Failed to add to portfolio');
            }
        })
        .catch(error => {
            showError('An error occurred: ' + error.message);
        });
    }
    
    /**
     * Show a loading indicator.
     */
    function showLoading(isLoading) {
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = isLoading ? 'block' : 'none';
        }
        
        // Disable/enable the run analysis button
        const runAnalysisBtn = document.getElementById('run-analysis-btn');
        if (runAnalysisBtn) {
            runAnalysisBtn.disabled = isLoading;
        }
    }
    
    /**
     * Show a success message.
     */
    function showSuccess(message) {
        const alertContainer = document.getElementById('alert-container');
        if (alertContainer) {
            alertContainer.innerHTML = `
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
        } else {
            console.log('Success: ' + message);
        }
    }
    
    /**
     * Show an error message.
     */
    function showError(message) {
        const alertContainer = document.getElementById('alert-container');
        if (alertContainer) {
            alertContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
        } else {
            console.error('Error: ' + message);
        }
    }
    
    // Public API
    return {
        init: init,
        runAnalysis: runAnalysis
    };
})();

// Initialize the analysis module when the DOM is loaded
document.addEventListener('DOMContentLoaded', Analysis.init);
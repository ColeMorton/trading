/**
 * Main application logic for Sensylate
 */

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up form handlers
    setupFormHandlers();
    
    // Set up UI event listeners
    setupUIEvents();
    
    // Update portfolio table initially
    refreshPortfolioTable();
    
    // Load sample data for demonstration
    loadSampleData();
    
    // Store for portfolio exports from MA Cross API
    window.portfolioExports = null;
});

/**
 * Sets up form handlers for the analysis form
 */
function setupFormHandlers() {
    // Analysis button click
    const runAnalysisBtn = document.getElementById('run-analysis-btn');
    if (runAnalysisBtn) {
        runAnalysisBtn.addEventListener('click', function(e) {
            e.preventDefault();
            runAnalysis();
        });
    }
    
    // Reset form button
    const resetFormBtn = document.getElementById('resetFormBtn');
    if (resetFormBtn) {
        resetFormBtn.addEventListener('click', function() {
            resetForm();
        });
    }
    
    // Export best portfolios button
    const exportBestBtn = document.getElementById('exportBestBtn');
    if (exportBestBtn) {
        exportBestBtn.addEventListener('click', function() {
            exportPortfolioCSV('best');
        });
    }
    
    // Load best portfolios button
    const loadBestBtn = document.getElementById('loadBestBtn');
    if (loadBestBtn) {
        loadBestBtn.addEventListener('click', function() {
            loadPortfoliosBest();
        });
    }
}

/**
 * Sets up UI event listeners
 */
function setupUIEvents() {
    // Toggle advanced configuration
    const toggleConfigBtn = document.getElementById('toggleConfigBtn');
    if (toggleConfigBtn) {
        toggleConfigBtn.addEventListener('click', function() {
            const advancedConfig = document.getElementById('advancedConfig');
            advancedConfig.classList.toggle('d-none');
            
            // Update button text
            if (advancedConfig.classList.contains('d-none')) {
                toggleConfigBtn.innerHTML = '<i class="fas fa-sliders-h me-1"></i> Toggle Advanced Config';
            } else {
                toggleConfigBtn.innerHTML = '<i class="fas fa-minus me-1"></i> Hide Advanced Config';
            }
        });
    }
    
    // Refresh table button
    const refreshTableBtn = document.getElementById('refreshTableBtn');
    if (refreshTableBtn) {
        refreshTableBtn.addEventListener('click', function() {
            refreshResultsTable();
        });
    }
    
    // Select all button
    const selectAllBtn = document.getElementById('selectAllBtn');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            selectAllRows(true);
        });
    }
    
    // Deselect all button
    const deselectAllBtn = document.getElementById('deselectAllBtn');
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', function() {
            selectAllRows(false);
        });
    }
    
    // Add to portfolio button
    const addToPortfolioBtn = document.getElementById('addToPortfolioBtn');
    if (addToPortfolioBtn) {
        addToPortfolioBtn.addEventListener('click', function() {
            addSelectedToPortfolio();
        });
    }
    
    // Clear portfolio button
    const clearPortfolioBtn = document.getElementById('clearPortfolioBtn');
    if (clearPortfolioBtn) {
        clearPortfolioBtn.addEventListener('click', function() {
            clearPortfolio();
        });
    }
    
    // Analyze portfolio button
    const analyzePortfolioBtn = document.getElementById('analyzePortfolioBtn');
    if (analyzePortfolioBtn) {
        analyzePortfolioBtn.addEventListener('click', function() {
            analyzePortfolio();
        });
    }
    
    // Weight modal slider
    const portfolioWeight = document.getElementById('portfolioWeight');
    if (portfolioWeight) {
        portfolioWeight.addEventListener('input', function() {
            const weightValue = document.getElementById('weightValue');
            if (weightValue) {
                weightValue.textContent = portfolioWeight.value;
            }
        });
    }
    
    // Save weight button
    const saveWeightBtn = document.getElementById('saveWeightBtn');
    if (saveWeightBtn) {
        saveWeightBtn.addEventListener('click', function() {
            savePortfolioWeight();
        });
    }
}

/**
 * Run the parameter sensitivity analysis
 */
function runAnalysis() {
    // Show loading indicator
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    document.getElementById('loadingResults').classList.remove('d-none');
    document.getElementById('noResults').classList.add('d-none');
    
    // Get form values
    const tickers = document.getElementById('tickers-input').value;
    
    // Build configuration object for MA Cross API
    const config = buildMACrossRequest(tickers);
    
    // Call MA Cross API
    fetch('http://127.0.0.1:8000/api/ma-cross/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => {
        if (response.status === 202) {
            // Async execution - poll for results
            return response.json().then(data => {
                showToast('Analysis Started', 'Analysis running in background. Please wait...', 'info');
                return pollForResults(data.execution_id);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // Process results
            processMACrossResults(data);
            
            // Show success notification
            showToast('Analysis Complete', `Analyzed ${data.total_portfolios_analyzed} portfolios, found ${data.total_portfolios_filtered} matching criteria.`, 'success');
        } else if (data.status === 'error') {
            // Show error
            showToast('Analysis Error', data.error || 'An error occurred during analysis.', 'error');
        }
    })
    .catch(error => {
        console.error('Error during analysis:', error);
        showToast('Analysis Error', 'Failed to connect to MA Cross API. Please ensure the API server is running.', 'error');
    })
    .finally(() => {
        // Hide loading indicator
        document.getElementById('loadingResults').classList.add('d-none');
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) loadingIndicator.style.display = 'none';
    });
}

/**
 * Build configuration object from form values
 */
function buildConfigFromForm() {
    // Get strategy types
    const strategyTypes = [];
    if (document.getElementById('sma-checkbox').checked) {
        strategyTypes.push('SMA');
    }
    if (document.getElementById('ema-checkbox').checked) {
        strategyTypes.push('EMA');
    }
    
    // Build configuration object
    const config = {
        WINDOWS: parseInt(document.getElementById('windows-input').value),
        REFRESH: true,
        STRATEGY_TYPES: strategyTypes,
        DIRECTION: document.getElementById('direction-select').value,
        USE_HOURLY: document.getElementById('use-hourly-checkbox').checked,
        USE_YEARS: document.getElementById('use-years-checkbox').checked,
        YEARS: parseInt(document.getElementById('years-input').value),
        USE_SYNTHETIC: document.getElementById('use-synthetic-checkbox').checked,
        USE_CURRENT: document.getElementById('use-current-checkbox').checked,
        USE_SCANNER: document.getElementById('use-scanner-checkbox').checked,
        MINIMUMS: {
            WIN_RATE: parseFloat(document.getElementById('min-win-rate-input').value),
            TRADES: parseInt(document.getElementById('min-trades-input').value),
            EXPECTANCY_PER_TRADE: parseFloat(document.getElementById('min-expectancy-input').value),
            PROFIT_FACTOR: parseFloat(document.getElementById('min-profit-factor-input').value),
            SORTINO_RATIO: parseFloat(document.getElementById('min-sortino-input').value),
        },
        SORT_BY: document.getElementById('sort-by-select').value,
        SORT_ASC: document.getElementById('sort-asc-checkbox').checked,
        USE_GBM: document.getElementById('use-gbm-checkbox').checked
    };
    
    // Add TICKER_2 if using synthetic
    if (config.USE_SYNTHETIC) {
        const ticker2Value = document.getElementById('ticker2-input').value.trim();
        if (ticker2Value) {
            config.TICKER_2 = ticker2Value;
        }
    }
    
    return config;
}

/**
 * Build MA Cross API request from form values
 */
function buildMACrossRequest(tickers) {
    const config = buildConfigFromForm();
    
    // Convert tickers to array
    const tickerArray = tickers.split(',').map(t => t.trim()).filter(t => t);
    
    // Build request matching MACrossRequest model
    const request = {
        TICKER: tickerArray.length === 1 ? tickerArray[0] : tickerArray,
        WINDOWS: config.WINDOWS,
        DIRECTION: config.DIRECTION,
        STRATEGY_TYPES: config.STRATEGY_TYPES,
        USE_HOURLY: config.USE_HOURLY,
        USE_YEARS: config.USE_YEARS,
        YEARS: config.YEARS,
        USE_SYNTHETIC: config.USE_SYNTHETIC,
        USE_CURRENT: config.USE_CURRENT,
        USE_SCANNER: config.USE_SCANNER,
        REFRESH: config.REFRESH,
        MINIMUMS: config.MINIMUMS,
        SORT_BY: config.SORT_BY,
        SORT_ASC: config.SORT_ASC,
        USE_GBM: config.USE_GBM,
        async_execution: false  // Start with sync execution
    };
    
    // Add TICKER_2 if present in config
    if (config.TICKER_2) {
        request.TICKER_2 = config.TICKER_2;
    }
    
    return request;
}

/**
 * Poll for async results
 */
async function pollForResults(executionId) {
    const maxAttempts = 60; // 5 minutes with 5 second intervals
    let attempts = 0;
    
    while (attempts < maxAttempts) {
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/ma-cross/status/${executionId}`);
            const data = await response.json();
            
            if (data.status === 'completed') {
                // Return the results in the expected format
                return {
                    status: 'success',
                    portfolios: data.results,
                    total_portfolios_analyzed: data.results ? data.results.length : 0,
                    total_portfolios_filtered: data.results ? data.results.length : 0
                };
            } else if (data.status === 'failed') {
                throw new Error(data.error || 'Analysis failed');
            }
            
            // Update progress message
            if (data.progress) {
                showToast('Analysis Progress', data.progress, 'info');
            }
            
            // Wait 5 seconds before next poll
            await new Promise(resolve => setTimeout(resolve, 5000));
            attempts++;
        } catch (error) {
            console.error('Error polling for results:', error);
            throw error;
        }
    }
    
    throw new Error('Analysis timeout - took too long to complete');
}

/**
 * Process MA Cross API results
 */
function processMACrossResults(data) {
    if (!data.portfolios || data.portfolios.length === 0) {
        showToast('No Results', 'No portfolios matched the criteria.', 'warning');
        return;
    }
    
    // Transform MA Cross results to match existing table format
    const transformedResults = data.portfolios.map(portfolio => ({
        'Ticker': portfolio.ticker,
        'Strategy Type': portfolio.strategy_type,
        'Short Window': portfolio.short_window,
        'Long Window': portfolio.long_window,
        'Score': portfolio.score,
        'Win Rate [%]': portfolio.win_rate * 100, // Convert to percentage
        'Profit Factor': portfolio.profit_factor,
        'Expectancy per Trade': portfolio.expectancy,
        'Sortino Ratio': portfolio.sortino_ratio,
        'Total Return [%]': portfolio.total_return,
        'Max Drawdown [%]': Math.abs(portfolio.max_drawdown), // Ensure positive
        'Total Trades': portfolio.total_trades,
        'Has Open Trade': portfolio.has_open_trade,
        'Has Signal Entry': portfolio.has_signal_entry
    }));
    
    // Populate results table
    populateResultsTable(transformedResults);
    
    // Store portfolio exports info if available
    if (data.portfolio_exports) {
        window.portfolioExports = data.portfolio_exports;
        
        // Show export/load buttons
        const loadBestBtn = document.getElementById('loadBestBtn');
        const exportBestBtn = document.getElementById('exportBestBtn');
        
        // Check for portfolios_best
        if (data.portfolio_exports.portfolios_best && data.portfolio_exports.portfolios_best.length > 0) {
            // Show buttons
            if (loadBestBtn) loadBestBtn.style.display = 'inline-block';
            if (exportBestBtn) exportBestBtn.style.display = 'inline-block';
            
            showToast('Best Portfolios Available', 
                `Found ${data.portfolio_exports.portfolios_best.length} best portfolio(s). Use Export to download.`, 
                'success');
        } else {
            // Hide buttons if no best portfolios
            if (loadBestBtn) loadBestBtn.style.display = 'none';
            if (exportBestBtn) exportBestBtn.style.display = 'none';
        }
    }
}

/**
 * Reset form to default values
 */
function resetForm() {
    // Reset form values to defaults
    document.getElementById('tickers-input').value = '';
    
    // Reset strategy types
    document.getElementById('sma-checkbox').checked = true;
    document.getElementById('ema-checkbox').checked = true;
    
    // Reset direction
    document.getElementById('direction').value = 'Long';
    
    // Reset advanced config
    document.getElementById('windows-input').value = defaultConfig.WINDOWS;
    document.getElementById('years-input').value = defaultConfig.YEARS;
    document.getElementById('sort-by-select').value = defaultConfig.SORT_BY;
    document.getElementById('sort-asc-checkbox').checked = defaultConfig.SORT_ASC;
    
    // Reset minimums
    document.getElementById('min-win-rate-input').value = defaultConfig.MINIMUMS.WIN_RATE;
    document.getElementById('min-trades-input').value = defaultConfig.MINIMUMS.TRADES;
    document.getElementById('min-expectancy-input').value = defaultConfig.MINIMUMS.EXPECTANCY_PER_TRADE;
    document.getElementById('min-profit-factor-input').value = defaultConfig.MINIMUMS.PROFIT_FACTOR;
    document.getElementById('min-sortino-input').value = defaultConfig.MINIMUMS.SORTINO_RATIO;
    
    // Reset checkboxes
    document.getElementById('use-hourly-checkbox').checked = defaultConfig.USE_HOURLY;
    document.getElementById('use-years-checkbox').checked = defaultConfig.USE_YEARS;
    document.getElementById('use-synthetic-checkbox').checked = defaultConfig.USE_SYNTHETIC;
    document.getElementById('use-current-checkbox').checked = defaultConfig.USE_CURRENT;
    document.getElementById('use-scanner-checkbox').checked = defaultConfig.USE_SCANNER;
    document.getElementById('use-gbm-checkbox').checked = defaultConfig.USE_GBM;
    
    // Reset ticker2 input
    document.getElementById('ticker2-input').value = defaultConfig.TICKER_2;
    
    // Show notification
    showToast('Form Reset', 'Form has been reset to default values.', 'info');
}

/**
 * Load sample data for demonstration
 */
function loadSampleData() {
    // For demonstration, load sample AAPL data
    fetch('/api/sample_data?ticker=AAPL')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                populateResultsTable(data.results);
            }
        })
        .catch(error => {
            console.error('Error loading sample data:', error);
        });
}

/**
 * Show a toast notification
 */
function showToast(title, message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastTitle = document.getElementById('toastTitle');
    const toastMessage = document.getElementById('toastMessage');
    
    // Set toast content
    toastTitle.textContent = title;
    toastMessage.textContent = message;
    
    // Set toast color based on type
    toast.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info');
    switch (type) {
        case 'success':
            toast.classList.add('bg-success');
            break;
        case 'error':
            toast.classList.add('bg-danger');
            break;
        case 'warning':
            toast.classList.add('bg-warning');
            break;
        default:
            toast.classList.add('bg-info');
    }
    
    // Create Bootstrap toast instance and show
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

/**
 * Export portfolio CSV files
 */
function exportPortfolioCSV(type = 'best') {
    if (!window.portfolioExports) {
        showToast('No Exports Available', 'Please run an analysis first to generate portfolio exports.', 'warning');
        return;
    }
    
    let exportPaths = [];
    if (type === 'best' && window.portfolioExports.portfolios_best) {
        exportPaths = window.portfolioExports.portfolios_best;
    } else if (type === 'filtered' && window.portfolioExports.portfolios_filtered) {
        exportPaths = window.portfolioExports.portfolios_filtered;
    } else if (type === 'all' && window.portfolioExports.portfolios) {
        exportPaths = window.portfolioExports.portfolios;
    }
    
    if (exportPaths.length === 0) {
        showToast('No Files Found', `No ${type} portfolio files available.`, 'warning');
        return;
    }
    
    // Download each file
    exportPaths.forEach(path => {
        const fileName = path.split('/').pop();
        const downloadUrl = `http://127.0.0.1:8000/api/data/${path}`;
        
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });
    
    showToast('Export Started', `Downloading ${exportPaths.length} ${type} portfolio file(s).`, 'success');
}

/**
 * Load portfolios_best CSV and display in results table
 */
async function loadPortfoliosBest() {
    if (!window.portfolioExports || !window.portfolioExports.portfolios_best) {
        showToast('No Best Portfolios', 'No best portfolio files available from the last analysis.', 'warning');
        return;
    }
    
    try {
        // Show loading
        document.getElementById('loadingResults').classList.remove('d-none');
        
        // Get the first best portfolio file
        const bestPath = window.portfolioExports.portfolios_best[0];
        const response = await fetch(`http://127.0.0.1:8000/api/data/${bestPath}`);
        
        if (!response.ok) {
            throw new Error('Failed to load portfolio file');
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && data.data) {
            // Transform CSV data to match table format
            const transformedData = data.data.map(row => ({
                'Ticker': row.Ticker || row.ticker,
                'Strategy Type': row['Strategy Type'] || row.strategy_type,
                'Short Window': row['Short Window'] || row.short_window,
                'Long Window': row['Long Window'] || row.long_window,
                'Score': parseFloat(row.Score || row.score),
                'Win Rate [%]': parseFloat(row['Win Rate [%]'] || row.win_rate),
                'Profit Factor': parseFloat(row['Profit Factor'] || row.profit_factor),
                'Expectancy per Trade': parseFloat(row['Expectancy per Trade'] || row.expectancy_per_trade),
                'Sortino Ratio': parseFloat(row['Sortino Ratio'] || row.sortino_ratio),
                'Total Return [%]': parseFloat(row['Total Return [%]'] || row.total_return),
                'Max Drawdown [%]': parseFloat(row['Max Drawdown [%]'] || row.max_drawdown),
                'Total Trades': parseInt(row['Total Trades'] || row.total_trades)
            }));
            
            populateResultsTable(transformedData);
            showToast('Best Portfolios Loaded', `Loaded ${transformedData.length} best portfolio(s).`, 'success');
        }
    } catch (error) {
        console.error('Error loading best portfolios:', error);
        showToast('Load Error', 'Failed to load best portfolio data.', 'error');
    } finally {
        document.getElementById('loadingResults').classList.add('d-none');
    }
}

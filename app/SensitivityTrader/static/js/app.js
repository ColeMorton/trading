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
});

/**
 * Sets up form handlers for the analysis form
 */
function setupFormHandlers() {
    // Analysis form submission
    const analysisForm = document.getElementById('analysisForm');
    if (analysisForm) {
        analysisForm.addEventListener('submit', function(e) {
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
    document.getElementById('loadingResults').classList.remove('d-none');
    document.getElementById('noResults').classList.add('d-none');
    
    // Get form values
    const tickers = document.getElementById('tickers').value;
    
    // Build configuration object
    const config = buildConfigFromForm();
    
    // For demonstration purposes, we'll load sample data
    // In a production environment, this would call the actual API
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
        if (data.status === 'success') {
            // Process results
            populateResultsTable(data.results);
            
            // Show success notification
            showToast('Analysis Complete', 'Parameter sensitivity analysis completed successfully.', 'success');
        } else {
            // Show error
            showToast('Analysis Error', data.message || 'An error occurred during analysis.', 'error');
        }
    })
    .catch(error => {
        console.error('Error during analysis:', error);
        showToast('Analysis Error', 'An unexpected error occurred. Please try again.', 'error');
    })
    .finally(() => {
        // Hide loading indicator
        document.getElementById('loadingResults').classList.add('d-none');
    });
}

/**
 * Build configuration object from form values
 */
function buildConfigFromForm() {
    // Get strategy types
    const strategyTypesSelect = document.getElementById('strategyTypes');
    const strategyTypes = Array.from(strategyTypesSelect.selectedOptions).map(option => option.value);
    
    // Build configuration object
    const config = {
        WINDOWS: parseInt(document.getElementById('windows').value),
        REFRESH: true,
        STRATEGY_TYPES: strategyTypes,
        DIRECTION: document.getElementById('direction').value,
        USE_HOURLY: document.getElementById('useHourly').checked,
        USE_YEARS: document.getElementById('useYears').checked,
        YEARS: parseInt(document.getElementById('years').value),
        USE_SYNTHETIC: document.getElementById('useSynthetic').checked,
        USE_CURRENT: true,
        MINIMUMS: {
            WIN_RATE: parseFloat(document.getElementById('minWinRate').value),
            TRADES: parseInt(document.getElementById('minTrades').value),
            EXPECTANCY_PER_TRADE: parseFloat(document.getElementById('minExpectancy').value),
            PROFIT_FACTOR: parseFloat(document.getElementById('minProfitFactor').value),
            SORTINO_RATIO: parseFloat(document.getElementById('minSortino').value),
        },
        SORT_BY: document.getElementById('sortBy').value,
        SORT_ASC: document.getElementById('sortDirection').value === 'asc',
        USE_GBM: document.getElementById('useGBM').checked
    };
    
    return config;
}

/**
 * Reset form to default values
 */
function resetForm() {
    // Reset form values to defaults
    document.getElementById('tickers').value = '';
    
    // Reset strategy types
    const strategyTypesSelect = document.getElementById('strategyTypes');
    Array.from(strategyTypesSelect.options).forEach(option => {
        option.selected = option.value === 'SMA';
    });
    
    // Reset direction
    document.getElementById('direction').value = 'Long';
    
    // Reset advanced config
    document.getElementById('windows').value = defaultConfig.WINDOWS;
    document.getElementById('years').value = defaultConfig.YEARS;
    document.getElementById('sortBy').value = defaultConfig.SORT_BY;
    document.getElementById('sortDirection').value = defaultConfig.SORT_ASC ? 'asc' : 'desc';
    
    // Reset minimums
    document.getElementById('minWinRate').value = defaultConfig.MINIMUMS.WIN_RATE;
    document.getElementById('minTrades').value = defaultConfig.MINIMUMS.TRADES;
    document.getElementById('minExpectancy').value = defaultConfig.MINIMUMS.EXPECTANCY_PER_TRADE;
    document.getElementById('minProfitFactor').value = defaultConfig.MINIMUMS.PROFIT_FACTOR;
    document.getElementById('minSortino').value = defaultConfig.MINIMUMS.SORTINO_RATIO;
    
    // Reset checkboxes
    document.getElementById('useHourly').checked = defaultConfig.USE_HOURLY;
    document.getElementById('useYears').checked = defaultConfig.USE_YEARS;
    document.getElementById('useSynthetic').checked = defaultConfig.USE_SYNTHETIC;
    document.getElementById('useGBM').checked = defaultConfig.USE_GBM;
    
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

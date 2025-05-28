/**
 * DataTables handling for Sensylate
 */

let resultsTable = null;
let portfolioTable = null;

/**
 * Initialize the results DataTable
 */
function initResultsTable() {
    // Destroy existing table if it exists
    if (resultsTable) {
        resultsTable.destroy();
    }
    
    // Initialize DataTable with options
    resultsTable = new DataTable('#resultsTable', {
        order: [[5, 'desc']], // Sort by score by default
        pageLength: 10,
        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
        columnDefs: [
            {
                targets: 0, // Select checkbox column
                orderable: false,
                className: 'select-checkbox',
                render: function() {
                    return '<div class="form-check"><input class="form-check-input select-row" type="checkbox"></div>';
                }
            },
            {
                targets: -1, // Actions column
                orderable: false,
                render: function() {
                    return '<button class="btn btn-sm btn-outline-primary add-to-portfolio-btn"><i class="fas fa-plus"></i></button>';
                }
            },
            {
                targets: [6, 10, 11], // Percentage columns
                render: function(data) {
                    return typeof data === 'number' ? data.toFixed(2) + '%' : data;
                }
            },
            {
                targets: [7, 8, 9], // Float columns
                render: function(data) {
                    return typeof data === 'number' ? data.toFixed(2) : data;
                }
            }
        ],
        responsive: true,
        language: {
            search: "Filter:",
            emptyTable: "No results available. Run an analysis to see data."
        },
        dom: '<"d-flex justify-content-between align-items-center mb-3"<"d-flex align-items-center"l><"d-flex"f>>t<"d-flex justify-content-between align-items-center mt-3"<"d-flex align-items-center"i><"d-flex"p>>',
        initComplete: function() {
            // Add event listeners to row checkboxes
            document.querySelectorAll('#resultsTable .select-row').forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    const row = this.closest('tr');
                    if (this.checked) {
                        row.classList.add('selected');
                    } else {
                        row.classList.remove('selected');
                    }
                });
            });
            
            // Add event listeners to add-to-portfolio buttons
            document.querySelectorAll('#resultsTable .add-to-portfolio-btn').forEach((button, index) => {
                button.addEventListener('click', function() {
                    addRowToPortfolio(index);
                });
            });
        }
    });
}

/**
 * Initialize the portfolio DataTable
 */
function initPortfolioTable() {
    // Destroy existing table if it exists
    if (portfolioTable) {
        portfolioTable.destroy();
    }
    
    // Initialize DataTable with options
    portfolioTable = new DataTable('#portfolioTable', {
        pageLength: 10,
        columnDefs: [
            {
                targets: [4], // Win Rate column
                render: function(data) {
                    return typeof data === 'number' ? data.toFixed(2) + '%' : data;
                }
            },
            {
                targets: [3, 5], // Float columns
                render: function(data) {
                    return typeof data === 'number' ? data.toFixed(2) : data;
                }
            },
            {
                targets: -1, // Actions column
                orderable: false,
                render: function(data, type, row, meta) {
                    return `
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary adjust-weight-btn" data-index="${meta.row}">
                                <i class="fas fa-balance-scale"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger remove-from-portfolio-btn" data-index="${meta.row}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    `;
                }
            }
        ],
        responsive: true,
        language: {
            search: "Filter:",
            emptyTable: "No items in portfolio. Add items from the results table."
        },
        dom: '<"d-flex justify-content-between align-items-center mb-3"<"d-flex align-items-center"l><"d-flex"f>>t<"d-flex justify-content-between align-items-center mt-3"<"d-flex align-items-center"i><"d-flex"p>>',
        initComplete: function() {
            addPortfolioTableEventListeners();
        },
        drawCallback: function() {
            addPortfolioTableEventListeners();
        }
    });
}

/**
 * Add event listeners to portfolio table buttons
 */
function addPortfolioTableEventListeners() {
    // Add event listeners to adjust weight buttons
    document.querySelectorAll('#portfolioTable .adjust-weight-btn').forEach(button => {
        button.addEventListener('click', function() {
            const index = this.getAttribute('data-index');
            showWeightModal(index);
        });
    });
    
    // Add event listeners to remove from portfolio buttons
    document.querySelectorAll('#portfolioTable .remove-from-portfolio-btn').forEach(button => {
        button.addEventListener('click', function() {
            const index = this.getAttribute('data-index');
            removeFromPortfolio(index);
        });
    });
}

/**
 * Populate the results table with data
 */
function populateResultsTable(results) {
    // Clear the table
    if (resultsTable) {
        resultsTable.clear();
    } else {
        initResultsTable();
    }
    
    // Hide empty state
    document.getElementById('noResults').classList.add('d-none');
    
    // Show/hide table container, header, and action buttons based on whether we have results
    const resultsActionsContainer = document.getElementById('results-actions-container');
    const tableResponsiveDiv = document.querySelector('#resultsTable').closest('.table-responsive');
    const resultsHeader = document.getElementById('results-header');
    
    if (results && results.length > 0) {
        document.querySelector('#resultsTable').classList.remove('d-none');
        // Show header when there are results
        if (resultsHeader) {
            resultsHeader.style.display = 'flex';
        }
        // Show table container when there are results
        if (tableResponsiveDiv) {
            tableResponsiveDiv.style.display = 'block';
        }
        // Show action buttons when there are results
        if (resultsActionsContainer) {
            resultsActionsContainer.style.display = 'flex';
        }
    } else {
        document.querySelector('#resultsTable').classList.add('d-none');
        // Hide header when there are no results
        if (resultsHeader) {
            resultsHeader.style.display = 'none';
        }
        // Hide table container when there are no results
        if (tableResponsiveDiv) {
            tableResponsiveDiv.style.display = 'none';
        }
        // Hide action buttons when there are no results
        if (resultsActionsContainer) {
            resultsActionsContainer.style.display = 'none';
        }
    }
    
    // Add data to the table
    if (Array.isArray(results) && results.length > 0) {
        results.forEach(result => {
            resultsTable.row.add([
                '', // Checkbox column
                result['Ticker'] || '',
                result['Strategy Type'] || '',
                result['Short Window'] || '',
                result['Long Window'] || '',
                result['Score'] || '',
                result['Win Rate [%]'] || '',
                result['Profit Factor'] || '',
                result['Expectancy per Trade'] || '',
                result['Sortino Ratio'] || '',
                result['Total Return [%]'] || '',
                result['Max Drawdown [%]'] || '',
                '' // Actions column
            ]);
        });
    }
    
    // Draw the table
    resultsTable.draw();
}

/**
 * Refresh the results table
 */
function refreshResultsTable() {
    // For demonstration, this just redraws the table
    // In a production environment, this could re-fetch data or apply new filters
    if (resultsTable) {
        resultsTable.draw();
        showToast('Table Refreshed', 'Results table has been refreshed.', 'info');
    }
}

/**
 * Refresh the portfolio table
 */
function refreshPortfolioTable() {
    // Fetch current portfolio from server
    fetch('/api/portfolio')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updatePortfolioTable(data.portfolio);
            }
        })
        .catch(error => {
            console.error('Error fetching portfolio:', error);
        });
}

/**
 * Update the portfolio table with data
 */
function updatePortfolioTable(portfolioItems) {
    // Initialize the table if it doesn't exist
    if (!portfolioTable) {
        initPortfolioTable();
    } else {
        // Clear the table
        portfolioTable.clear();
    }
    
    // Toggle visibility of empty state message
    if (portfolioItems.length === 0) {
        document.getElementById('emptyPortfolio').classList.remove('d-none');
        document.querySelector('#portfolioTable').classList.add('d-none');
    } else {
        document.getElementById('emptyPortfolio').classList.add('d-none');
        document.querySelector('#portfolioTable').classList.remove('d-none');
        
        // Add data to the table
        portfolioItems.forEach(item => {
            portfolioTable.row.add([
                item['Ticker'] || '',
                item['Strategy Type'] || '',
                `${item['Short Window'] || ''} / ${item['Long Window'] || ''}`,
                item['Score'] || '',
                item['Win Rate [%]'] || '',
                item['Expectancy per Trade'] || '',
                item['weight'] || 1,
                '' // Actions column
            ]);
        });
    }
    
    // Draw the table
    portfolioTable.draw();
}

/**
 * Select or deselect all rows in the results table
 */
function selectAllRows(selected) {
    document.querySelectorAll('#resultsTable .select-row').forEach(checkbox => {
        checkbox.checked = selected;
        const row = checkbox.closest('tr');
        if (selected) {
            row.classList.add('selected');
        } else {
            row.classList.remove('selected');
        }
    });
    
    showToast(
        selected ? 'All Selected' : 'All Deselected',
        selected ? 'All rows have been selected.' : 'All rows have been deselected.',
        'info'
    );
}

/**
 * Add selected rows to portfolio
 */
function addSelectedToPortfolio() {
    const selectedCheckboxes = document.querySelectorAll('#resultsTable .select-row:checked');
    
    if (selectedCheckboxes.length === 0) {
        showToast('No Selection', 'Please select at least one row to add to portfolio.', 'warning');
        return;
    }
    
    // For each selected checkbox, get the corresponding row data
    let addedCount = 0;
    selectedCheckboxes.forEach((checkbox, index) => {
        const row = checkbox.closest('tr');
        const rowIndex = resultsTable.row(row).index();
        
        if (rowIndex !== undefined) {
            addRowToPortfolio(rowIndex);
            addedCount++;
        }
    });
    
    // Show success message
    showToast('Added to Portfolio', `${addedCount} item(s) added to portfolio.`, 'success');
}

/**
 * Add a specific row to the portfolio
 */
function addRowToPortfolio(rowIndex) {
    if (!resultsTable) return;
    
    // Get row data
    const rowData = resultsTable.row(rowIndex).data();
    if (!rowData) return;
    
    // Create portfolio item object
    const portfolioItem = {
        'Ticker': rowData[1],
        'Strategy Type': rowData[2],
        'Short Window': parseInt(rowData[3]),
        'Long Window': parseInt(rowData[4]),
        'Score': parseFloat(rowData[5]),
        'Win Rate [%]': parseFloat(rowData[6]),
        'Profit Factor': parseFloat(rowData[7]),
        'Expectancy per Trade': parseFloat(rowData[8]),
        'Sortino Ratio': parseFloat(rowData[9]),
        'Total Return [%]': parseFloat(rowData[10]),
        'Max Drawdown [%]': parseFloat(rowData[11]),
        'weight': 1 // Default weight
    };
    
    // Add to portfolio via API
    fetch('/api/portfolio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(portfolioItem)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update portfolio table
            updatePortfolioTable(data.portfolio);
        }
    })
    .catch(error => {
        console.error('Error adding to portfolio:', error);
        showToast('Error', 'Failed to add item to portfolio.', 'error');
    });
}

/**
 * Show the weight adjustment modal
 */
function showWeightModal(index) {
    // Set the item index in the hidden field
    document.getElementById('weightItemIndex').value = index;
    
    // Get the current weight from the table
    const currentWeight = portfolioTable.row(index).data()[6] || 1;
    
    // Set the slider value
    const weightSlider = document.getElementById('portfolioWeight');
    weightSlider.value = currentWeight;
    
    // Update the display value
    document.getElementById('weightValue').textContent = currentWeight;
    
    // Show the modal
    const weightModal = new bootstrap.Modal(document.getElementById('weightModal'));
    weightModal.show();
}

/**
 * Save the portfolio weight
 */
function savePortfolioWeight() {
    const index = document.getElementById('weightItemIndex').value;
    const weight = parseInt(document.getElementById('portfolioWeight').value);
    
    if (index === '' || isNaN(weight)) {
        return;
    }
    
    // Get the portfolio item data
    const rowData = portfolioTable.row(index).data();
    if (!rowData) return;
    
    // Create portfolio item object with updated weight
    const portfolioItem = {
        'Ticker': rowData[0],
        'Strategy Type': rowData[1],
        'Short Window': parseInt(rowData[2].split(' / ')[0]),
        'Long Window': parseInt(rowData[2].split(' / ')[1]),
        'weight': weight
    };
    
    // Update portfolio item via API
    fetch('/api/portfolio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(portfolioItem)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update portfolio table
            updatePortfolioTable(data.portfolio);
            
            // Hide the modal
            const weightModal = bootstrap.Modal.getInstance(document.getElementById('weightModal'));
            weightModal.hide();
            
            // Show success message
            showToast('Weight Updated', 'Portfolio item weight has been updated.', 'success');
        }
    })
    .catch(error => {
        console.error('Error updating portfolio weight:', error);
        showToast('Error', 'Failed to update portfolio weight.', 'error');
    });
}

/**
 * Remove an item from the portfolio
 */
function removeFromPortfolio(index) {
    // Get the portfolio item data
    const rowData = portfolioTable.row(index).data();
    if (!rowData) return;
    
    // Create portfolio item object for identification
    const portfolioItem = {
        'Ticker': rowData[0],
        'Strategy Type': rowData[1],
        'Short Window': parseInt(rowData[2].split(' / ')[0]),
        'Long Window': parseInt(rowData[2].split(' / ')[1])
    };
    
    // Remove from portfolio via API
    fetch('/api/portfolio', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(portfolioItem)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update portfolio table
            updatePortfolioTable(data.portfolio);
            
            // Show success message
            showToast('Removed from Portfolio', 'Item has been removed from portfolio.', 'info');
        }
    })
    .catch(error => {
        console.error('Error removing from portfolio:', error);
        showToast('Error', 'Failed to remove item from portfolio.', 'error');
    });
}

/**
 * Clear the entire portfolio
 */
function clearPortfolio() {
    // Show confirmation
    if (!confirm('Are you sure you want to clear the entire portfolio?')) {
        return;
    }
    
    // Clear portfolio via API
    fetch('/api/portfolio/clear', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update portfolio table
            updatePortfolioTable([]);
            
            // Reset portfolio analysis
            document.getElementById('portfolioAnalysis').innerHTML = '<p class="text-center text-muted">Add items to your portfolio and click "Analyze Portfolio" to see metrics.</p>';
            
            // Clear charts
            clearPortfolioCharts();
            
            // Show success message
            showToast('Portfolio Cleared', 'Your portfolio has been cleared.', 'info');
        }
    })
    .catch(error => {
        console.error('Error clearing portfolio:', error);
        showToast('Error', 'Failed to clear portfolio.', 'error');
    });
}

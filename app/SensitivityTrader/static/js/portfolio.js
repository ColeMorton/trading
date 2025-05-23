/**
 * Portfolio management functions for Sensylate
 */

/**
 * Analyze the current portfolio
 */
function analyzePortfolio() {
    // Check if there are items in the portfolio
    if (document.getElementById('emptyPortfolio').classList.contains('d-none') === false) {
        showToast('Empty Portfolio', 'Please add items to your portfolio before analyzing.', 'warning');
        return;
    }
    
    // Show loading indicator
    document.getElementById('portfolioAnalysis').innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Analyzing portfolio...</p>
        </div>
    `;
    
    // Analyze portfolio via API
    fetch('/api/portfolio/analyze', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            displayPortfolioAnalysis(data.analysis);
        } else {
            // Show error
            document.getElementById('portfolioAnalysis').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    ${data.message || 'An error occurred during portfolio analysis.'}
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error analyzing portfolio:', error);
        document.getElementById('portfolioAnalysis').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                An unexpected error occurred. Please try again.
            </div>
        `;
    });
}

/**
 * Display the portfolio analysis results
 */
function displayPortfolioAnalysis(analysis) {
    if (!analysis || analysis.error) {
        document.getElementById('portfolioAnalysis').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                ${analysis.error || 'An error occurred during analysis.'}
            </div>
        `;
        return;
    }
    
    // Display formatted metrics
    const metrics = analysis.formatted;
    
    document.getElementById('portfolioAnalysis').innerHTML = `
        <div class="card mb-3 bg-dark">
            <div class="card-body">
                <h5 class="card-title text-center">Portfolio Score</h5>
                <div class="display-4 text-center text-primary">${analysis.score}</div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-6">
                <div class="mb-3">
                    <label class="form-label fw-bold">Win Rate</label>
                    <div>${metrics.win_rate}</div>
                </div>
            </div>
            <div class="col-6">
                <div class="mb-3">
                    <label class="form-label fw-bold">Expectancy</label>
                    <div>${metrics.expectancy}</div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-6">
                <div class="mb-3">
                    <label class="form-label fw-bold">Profit Factor</label>
                    <div>${metrics.profit_factor}</div>
                </div>
            </div>
            <div class="col-6">
                <div class="mb-3">
                    <label class="form-label fw-bold">Sortino Ratio</label>
                    <div>${metrics.sortino_ratio}</div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-6">
                <div class="mb-3">
                    <label class="form-label fw-bold">Total Return</label>
                    <div>${metrics.total_return}</div>
                </div>
            </div>
            <div class="col-6">
                <div class="mb-3">
                    <label class="form-label fw-bold">Max Drawdown</label>
                    <div>${metrics.max_drawdown}</div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-12">
                <div class="mb-3">
                    <label class="form-label fw-bold">Diversity</label>
                    <div>${metrics.ticker_diversity}</div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-6">
                <div class="mb-3">
                    <label class="form-label fw-bold">Strategies</label>
                    <div>${metrics.strategy_diversity}</div>
                </div>
            </div>
            <div class="col-6">
                <div class="mb-3">
                    <label class="form-label fw-bold">Most Common</label>
                    <div>${metrics.most_common_ticker}</div>
                </div>
            </div>
        </div>
    `;
    
    // Create charts
    createPortfolioCharts(analysis);
    
    // Show success notification
    showToast('Analysis Complete', 'Portfolio analysis completed successfully.', 'success');
}

/**
 * Create portfolio charts
 */
function createPortfolioCharts(analysis) {
    // Clear existing charts
    clearPortfolioCharts();
    
    // Create metrics radar chart
    createMetricsChart(analysis);
    
    // Create diversity pie chart
    createDiversityChart(analysis);
}

/**
 * Create the metrics radar chart
 */
function createMetricsChart(analysis) {
    const ctx = document.getElementById('portfolioMetricsChart').getContext('2d');
    
    // Calculate normalized metrics (0-100)
    const rawMetrics = analysis.raw;
    const normalizedMetrics = {
        win_rate: rawMetrics.win_rate * 100, // Convert from 0-1 to 0-100
        expectancy: Math.min(rawMetrics.expectancy * 10, 100), // Scale and cap at 100
        profit_factor: Math.min(rawMetrics.profit_factor * 20, 100), // Scale and cap at 100
        sortino_ratio: Math.min(rawMetrics.sortino_ratio * 33.3, 100), // Scale and cap at 100
        drawdown_protection: 100 - rawMetrics.max_drawdown // Inverse of drawdown
    };
    
    // Create chart
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: [
                'Win Rate',
                'Expectancy',
                'Profit Factor',
                'Sortino Ratio',
                'Drawdown Protection'
            ],
            datasets: [{
                label: 'Portfolio Metrics',
                data: [
                    normalizedMetrics.win_rate,
                    normalizedMetrics.expectancy,
                    normalizedMetrics.profit_factor,
                    normalizedMetrics.sortino_ratio,
                    normalizedMetrics.drawdown_protection
                ],
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    pointLabels: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    ticks: {
                        backdropColor: 'transparent',
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.raw.toFixed(1)}%`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create the diversity pie chart
 */
function createDiversityChart(analysis) {
    const ctx = document.getElementById('portfolioDiversityChart').getContext('2d');
    
    // Get ticker counts
    const tickerCounts = analysis.raw.ticker_counts;
    
    // Prepare data for chart
    const labels = Object.keys(tickerCounts);
    const data = Object.values(tickerCounts);
    
    // Generate colors
    const colors = generateColors(labels.length);
    
    // Create chart
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                title: {
                    display: true,
                    text: 'Portfolio Composition',
                    color: 'rgba(255, 255, 255, 0.7)'
                }
            }
        }
    });
}

/**
 * Generate colors for chart
 */
function generateColors(count) {
    const colors = [];
    const baseHues = [210, 120, 0, 270, 30, 180, 330, 60, 240, 90];
    
    for (let i = 0; i < count; i++) {
        const hue = baseHues[i % baseHues.length];
        const lightness = 50 + (i % 3) * 10;
        colors.push(`hsl(${hue}, 70%, ${lightness}%)`);
    }
    
    return colors;
}

/**
 * Clear portfolio charts
 */
function clearPortfolioCharts() {
    // Get chart canvases
    const metricsCanvas = document.getElementById('portfolioMetricsChart');
    const diversityCanvas = document.getElementById('portfolioDiversityChart');
    
    // Destroy existing charts
    Chart.getChart(metricsCanvas)?.destroy();
    Chart.getChart(diversityCanvas)?.destroy();
}

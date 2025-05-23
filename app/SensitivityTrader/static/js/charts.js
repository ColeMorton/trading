/**
 * Chart utilities for Sensylate
 */

/**
 * Create a performance comparison chart
 */
function createPerformanceChart(elementId, data) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Value'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            }
        }
    });
}

/**
 * Create a correlation heatmap
 */
function createCorrelationHeatmap(elementId, data) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    new Chart(ctx, {
        type: 'matrix',
        data: {
            datasets: [{
                data: data.values,
                width: data.labels.length,
                height: data.labels.length,
                xLabels: data.labels,
                yLabels: data.labels
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function() {
                            return '';
                        },
                        label: function(context) {
                            const i = context.dataIndex % data.labels.length;
                            const j = Math.floor(context.dataIndex / data.labels.length);
                            return `${data.labels[i]} vs ${data.labels[j]}: ${context.raw.v.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        callback: function(value, index) {
                            return data.labels[index];
                        },
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    ticks: {
                        callback: function(value, index) {
                            return data.labels[index];
                        },
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        display: false
                    },
                    reverse: true
                }
            }
        }
    });
}

/**
 * Create a parameter sensitivity heatmap
 */
function createSensitivityHeatmap(elementId, data) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    new Chart(ctx, {
        type: 'matrix',
        data: {
            datasets: [{
                data: data.values,
                width: data.x.length,
                height: data.y.length,
                xLabels: data.x,
                yLabels: data.y
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const i = context[0].dataIndex % data.x.length;
                            const j = Math.floor(context[0].dataIndex / data.x.length);
                            return `Short: ${data.x[i]}, Long: ${data.y[j]}`;
                        },
                        label: function(context) {
                            return `Score: ${context.raw.v.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Short Window',
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    ticks: {
                        callback: function(value, index) {
                            return data.x[index];
                        },
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Long Window',
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    ticks: {
                        callback: function(value, index) {
                            return data.y[index];
                        },
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        display: false
                    },
                    reverse: true
                }
            }
        }
    });
}

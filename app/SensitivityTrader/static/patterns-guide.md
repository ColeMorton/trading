# Sensylate UI Patterns Guide

## Introduction

This guide documents the common UI patterns and component usage within Sensylate. It serves as a practical reference for implementing consistent interfaces across the application. While the style guide defines the visual language, this patterns guide focuses on how these elements should be composed together in context.

## Table of Contents

1. [Page Structure](#page-structure)
2. [Navigation Patterns](#navigation-patterns)
3. [Analysis Configuration Patterns](#analysis-configuration-patterns)
4. [Results Display Patterns](#results-display-patterns)
5. [Portfolio Management Patterns](#portfolio-management-patterns)
6. [Data Visualization Patterns](#data-visualization-patterns)
7. [Form Patterns](#form-patterns)
8. [Feedback Patterns](#feedback-patterns)
9. [Responsive Behavior Patterns](#responsive-behavior-patterns)

## Page Structure

### Main Layout

All pages within Sensylate follow this structural hierarchy:

1. **Navigation Header**: Fixed at the top
2. **Main Content Area**: Comprised of cards in a fluid layout
3. **Footer**: Fixed at the bottom

```html
<header>
  <nav class="navbar navbar-dark bg-dark">
    <!-- Navigation content -->
  </nav>
</header>

<main class="container-fluid py-4">
  <!-- Main content cards -->
</main>

<footer class="footer mt-auto py-3 bg-dark">
  <!-- Footer content -->
</footer>
```

### Section Structure

Each main section is contained within a card that includes:

1. **Card Header**: With section title and optional action buttons
2. **Card Body**: Main content area
3. **Optional Card Footer**: For actions related to the entire section

```html
<div class="card mb-4">
  <div class="card-header d-flex justify-content-between align-items-center">
    <h5 class="mb-0">
      <i class="fas fa-[icon] me-2"></i> Section Title
    </h5>
    <div>
      <!-- Action buttons -->
    </div>
  </div>
  <div class="card-body">
    <!-- Section content -->
  </div>
</div>
```

## Navigation Patterns

### Main Navigation

- The main navigation should always be at the top of the page
- Use clearly labeled links for primary sections
- Include appropriate icons before text labels
- For mobile, collapse into a hamburger menu

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container-fluid">
    <a class="navbar-brand" href="/">
      <i class="fas fa-chart-line me-2"></i> Sensylate
    </a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav">
        <li class="nav-item">
          <a class="nav-link active" aria-current="page" href="/">Parameter Testing</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#portfolio-section">Portfolio Builder</a>
        </li>
      </ul>
    </div>
  </div>
</nav>
```

### Page Section Navigation

- Use anchor links to navigate to different sections on the same page
- Ensure adequate spacing between sections (2rem minimum)
- Add section dividers where needed

```html
<a href="#portfolio-section" class="btn btn-primary">
  <i class="fas fa-briefcase me-1"></i> Go to Portfolio
</a>

<!-- Later in the page -->
<div id="portfolio-section" class="pt-2 mt-4">
  <!-- Portfolio section content -->
</div>
```

## Analysis Configuration Patterns

### Parameter Input Forms

Analysis forms should follow these patterns:

1. **Group Related Inputs**: Use row and column layouts to group related parameters
2. **Progressive Disclosure**: Hide advanced options by default
3. **Defaults**: Always provide sensible default values
4. **Input Validation**: Validate inputs in real-time where possible
5. **Responsive Layout**: Stack inputs vertically on mobile

```html
<form id="analysisForm">
  <!-- Basic parameters (always visible) -->
  <div class="row">
    <div class="col-md-4">
      <div class="mb-3">
        <label for="tickers" class="form-label">Ticker(s)</label>
        <input type="text" class="form-control" id="tickers" placeholder="Enter tickers separated by commas">
        <div class="form-text">For demo, try "AAPL" or "CRYPTO"</div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="mb-3">
        <label for="strategyTypes" class="form-label">Strategy Types</label>
        <select class="form-select" id="strategyTypes" multiple>
          <option value="SMA" selected>SMA</option>
          <option value="EMA">EMA</option>
          <option value="MACD">MACD</option>
        </select>
      </div>
    </div>
  </div>
  
  <!-- Toggle for advanced options -->
  <button class="btn btn-sm btn-outline-primary mb-3" id="toggleConfigBtn">
    <i class="fas fa-sliders-h me-1"></i> Toggle Advanced Config
  </button>
  
  <!-- Advanced parameters (hidden by default) -->
  <div id="advancedConfig" class="d-none">
    <!-- Advanced parameter inputs -->
  </div>
  
  <!-- Form actions -->
  <div class="d-flex justify-content-between mt-3">
    <button type="button" class="btn btn-secondary" id="resetFormBtn">
      <i class="fas fa-undo me-1"></i> Reset
    </button>
    <button type="submit" class="btn btn-primary" id="runAnalysisBtn">
      <i class="fas fa-play me-1"></i> Run Analysis
    </button>
  </div>
</form>
```

### Configuration Options

Standard configuration inputs should include:

1. **Ticker Input**: Text input for ticker symbols
2. **Strategy Selection**: Multi-select for strategy types
3. **Window Parameters**: Numeric inputs for lookback periods
4. **Minimum Requirements**: Numeric inputs for filtering criteria
5. **Sorting Options**: Dropdown for sort field and direction

## Results Display Patterns

### Results Table

Results tables should:

1. **Use DataTables**: For sorting, filtering, and pagination
2. **Include Selection**: Checkboxes for multi-select functionality
3. **Format Numbers**: Properly format percentages and decimals
4. **Provide Actions**: Row-level action buttons
5. **Highlight Selections**: Visual indication of selected rows

```html
<div class="table-responsive">
  <table id="resultsTable" class="table table-striped table-hover">
    <thead>
      <tr>
        <th>Select</th>
        <th>Ticker</th>
        <th>Strategy</th>
        <th>Short Window</th>
        <th>Long Window</th>
        <th>Score</th>
        <th>Win Rate</th>
        <th>Profit Factor</th>
        <th>Expectancy</th>
        <th>Sortino Ratio</th>
        <th>Total Return</th>
        <th>Max Drawdown</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <!-- Results rows will be populated dynamically -->
    </tbody>
  </table>
</div>
```

### Batch Actions

For operations that affect multiple selected items:

1. **Selection Controls**: Buttons to select/deselect all
2. **Batch Actions**: Prominently displayed above the table
3. **Action Confirmation**: Confirm destructive batch operations
4. **Selection Count**: Show number of selected items

```html
<div class="mb-3">
  <button class="btn btn-sm btn-outline-secondary" id="selectAllBtn">
    <i class="fas fa-check-square me-1"></i> Select All
  </button>
  <button class="btn btn-sm btn-outline-danger" id="deselectAllBtn">
    <i class="fas fa-square me-1"></i> Deselect All
  </button>
  <button class="btn btn-sm btn-primary" id="addToPortfolioBtn">
    <i class="fas fa-plus me-1"></i> Add Selected to Portfolio
  </button>
</div>
```

### Loading States

Always provide clear loading indicators:

1. **Initial Loading**: Show spinner when data is first loading
2. **Empty States**: Display helpful message when no results exist
3. **Loading Overlay**: Show overlay during processing
4. **Progress Indication**: For long operations, show progress

```html
<!-- Loading state -->
<div id="loadingResults" class="text-center my-5">
  <div class="spinner-border text-primary" role="status">
    <span class="visually-hidden">Loading...</span>
  </div>
  <p class="mt-2">Processing analysis, please wait...</p>
</div>

<!-- Empty state -->
<div id="noResults" class="text-center my-5">
  <i class="fas fa-search fa-3x mb-3 text-muted"></i>
  <p>No results yet. Run an analysis to see data here.</p>
</div>
```

## Portfolio Management Patterns

### Portfolio Table

The portfolio table should:

1. **Show Key Metrics**: Display essential metrics for each item
2. **Include Weights**: Show and allow adjustment of weights
3. **Provide Actions**: Allow removing items or adjusting weights
4. **Format Consistently**: Use same formatting as results table

```html
<div class="table-responsive">
  <table id="portfolioTable" class="table table-striped table-hover">
    <thead>
      <tr>
        <th>Ticker</th>
        <th>Strategy</th>
        <th>Windows</th>
        <th>Score</th>
        <th>Win Rate</th>
        <th>Expectancy</th>
        <th>Weight</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <!-- Portfolio items will be populated dynamically -->
    </tbody>
  </table>
</div>
```

### Weight Adjustment

For adjusting portfolio weights:

1. **Use Modal**: Show weight adjustment in a modal dialog
2. **Range Slider**: Use slider for intuitive weight adjustment
3. **Value Display**: Show current weight value
4. **Save/Cancel**: Include clear actions to save or cancel

```html
<!-- Weight adjustment modal -->
<div class="modal fade" id="weightModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Adjust Portfolio Weight</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        <p>Adjust the weight of this item in your portfolio:</p>
        <input type="hidden" id="weightItemIndex" value="">
        <div class="d-flex align-items-center">
          <input type="range" class="form-range flex-grow-1 me-2" min="1" max="10" value="1" id="portfolioWeight">
          <span id="weightValue">1</span>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-primary" id="saveWeightBtn">Save</button>
      </div>
    </div>
  </div>
</div>
```

### Portfolio Analysis

For displaying portfolio analysis:

1. **Summary Card**: Show key portfolio metrics
2. **Visual Charts**: Include radar and pie charts
3. **Detailed Metrics**: List all relevant metrics with labels
4. **Clear Sections**: Separate metrics logically
5. **Score Highlight**: Prominently display overall score

```html
<div class="card">
  <div class="card-header">
    <h6 class="mb-0">Portfolio Analysis</h6>
  </div>
  <div class="card-body">
    <div class="card mb-3 bg-dark">
      <div class="card-body">
        <h5 class="card-title text-center">Portfolio Score</h5>
        <div class="display-4 text-center text-primary">86.5/100</div>
      </div>
    </div>
    
    <!-- Metrics grid -->
    <div class="row">
      <!-- Metrics displayed in a grid layout -->
    </div>
    
    <!-- Charts -->
    <div class="mt-4">
      <canvas id="portfolioMetricsChart"></canvas>
      <canvas id="portfolioDiversityChart" class="mt-3"></canvas>
    </div>
  </div>
</div>
```

## Data Visualization Patterns

### Chart Layouts

Charts should:

1. **Use Consistent Size**: Height of 300px on desktop, 250px on mobile
2. **Include Clear Labels**: Axis labels, titles, and legends
3. **Support Interaction**: Tooltips on hover
4. **Use Consistent Colors**: Follow color palette
5. **Have Appropriate Spacing**: Margin of 1.5rem between charts

### Chart Type Selection

Use the appropriate chart type based on the data:

1. **Line Charts**: For time series and trends
2. **Bar Charts**: For comparing discrete values
3. **Radar Charts**: For multivariate performance metrics
4. **Pie/Donut Charts**: For composition and allocation

```javascript
// Radar chart for portfolio metrics
function createMetricsChart(analysis) {
  const ctx = document.getElementById('portfolioMetricsChart').getContext('2d');
  
  // Calculate normalized metrics (0-100)
  const rawMetrics = analysis.raw;
  const normalizedMetrics = {
    win_rate: rawMetrics.win_rate * 100,
    expectancy: Math.min(rawMetrics.expectancy * 10, 100),
    profit_factor: Math.min(rawMetrics.profit_factor * 20, 100),
    sortino_ratio: Math.min(rawMetrics.sortino_ratio * 33.3, 100),
    drawdown_protection: 100 - rawMetrics.max_drawdown
  };
  
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
        borderWidth: 2
      }]
    },
    options: {
      // Chart options
    }
  });
}
```

## Form Patterns

### Form Layout

Forms should follow these patterns:

1. **Logical Grouping**: Group related inputs together
2. **Consistent Spacing**: 1rem (16px) between form groups
3. **Label Positioning**: Labels above inputs, not inline
4. **Helpful Text**: Include helper text for complex inputs
5. **Validation Feedback**: Show validation errors inline

### Input States

All form inputs should properly indicate:

1. **Default State**: Standard styling
2. **Focus State**: Clear indication when focused
3. **Disabled State**: Visually distinct when disabled
4. **Error State**: Red highlight with error message
5. **Success State**: Green highlight for validated inputs

```html
<div class="mb-3">
  <label for="inputExample" class="form-label">Input Label</label>
  <input type="text" class="form-control" id="inputExample">
  <div class="form-text">Helper text with additional information</div>
</div>

<div class="mb-3">
  <label for="inputWithError" class="form-label">Input with Error</label>
  <input type="text" class="form-control is-invalid" id="inputWithError">
  <div class="invalid-feedback">Error message goes here</div>
</div>

<div class="mb-3">
  <label for="inputWithSuccess" class="form-label">Input with Success</label>
  <input type="text" class="form-control is-valid" id="inputWithSuccess">
  <div class="valid-feedback">Success message goes here</div>
</div>

<div class="mb-3">
  <label for="disabledInput" class="form-label">Disabled Input</label>
  <input type="text" class="form-control" id="disabledInput" disabled>
</div>
```

## Feedback Patterns

### Toast Notifications

Use toast notifications for:

1. **Success Messages**: After completing operations
2. **Error Messages**: When operations fail
3. **Information Messages**: For system status updates
4. **Warning Messages**: For potential issues

```javascript
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
```

Toast HTML structure:

```html
<div class="toast-container position-fixed top-0 end-0 p-3">
  <div id="toast" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
    <div class="toast-header">
      <strong class="me-auto" id="toastTitle">Notification</strong>
      <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
    <div class="toast-body" id="toastMessage">
      Message content goes here
    </div>
  </div>
</div>
```

### Loading Indicators

Use appropriate loading indicators:

1. **Spinner**: For loading data or processing
2. **Progress Bar**: For operations with known progress
3. **Skeleton Screens**: For initial page loading
4. **Disabled Buttons**: Show loading state in buttons

```html
<!-- Button with loading state -->
<button class="btn btn-primary" type="button" disabled>
  <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
  Loading...
</button>

<!-- Spinner for section loading -->
<div class="d-flex justify-content-center my-4">
  <div class="spinner-border text-primary" role="status">
    <span class="visually-hidden">Loading...</span>
  </div>
</div>

<!-- Progress bar for known progress -->
<div class="progress mb-3">
  <div class="progress-bar" role="progressbar" style="width: 75%" aria-valuenow="75" aria-valuemin="0" aria-valuemax="100">75%</div>
</div>
```

## Responsive Behavior Patterns

### Mobile Adaptations

On mobile devices:

1. **Stack Columns**: Columns should stack vertically
2. **Adjust Font Sizes**: Reduce headings by 10-15%
3. **Simplify Tables**: Hide less important columns
4. **Increase Touch Targets**: Minimum 44px × 44px
5. **Adjust Spacing**: Reduce margins and padding proportionally

### Navigation Changes

For mobile navigation:

1. **Collapse to Hamburger**: Use hamburger menu under 992px
2. **Simplify Menu**: Reduce or combine menu items
3. **Fixed Position**: Keep navbar accessible at top
4. **Back to Top**: Add back-to-top button on long pages

### Content Prioritization

Prioritize content on smaller screens:

1. **Critical Controls First**: Show most important controls at top
2. **Progressive Disclosure**: Hide advanced options by default
3. **Summarize Data**: Show summaries instead of full details
4. **Focused Charts**: Simplify or focus charts on key metrics

```html
<!-- Example of responsive utility classes -->
<div class="d-none d-md-block">
  <!-- This content only shows on medium screens and larger -->
</div>

<div class="d-md-none">
  <!-- This content only shows on screens smaller than medium -->
</div>

<!-- Responsive table that scrolls horizontally on small screens -->
<div class="table-responsive">
  <table class="table">
    <!-- Table content -->
  </table>
</div>
```

### Responsive Testing Points

Always test responsive behavior at these breakpoints:

1. **Extra small**: < 576px (Mobile portrait)
2. **Small**: 576px - 767px (Mobile landscape)
3. **Medium**: 768px - 991px (Tablets)
4. **Large**: 992px - 1199px (Desktops)
5. **Extra large**: ≥ 1200px (Large desktops)

---

## Implementation Example: Analysis Section

Here's a complete example of how to implement the analysis section following the patterns above:

```html
<div class="card mb-4">
  <div class="card-header d-flex justify-content-between align-items-center">
    <h5 class="mb-0">
      <i class="fas fa-cogs me-2"></i> Parameter Sensitivity Testing
    </h5>
    <div>
      <button class="btn btn-sm btn-outline-primary" id="toggleConfigBtn">
        <i class="fas fa-sliders-h me-1"></i> Toggle Advanced Config
      </button>
    </div>
  </div>
  <div class="card-body">
    <form id="analysisForm">
      <div class="row">
        <div class="col-md-4">
          <div class="mb-3">
            <label for="tickers" class="form-label">Ticker(s)</label>
            <input type="text" class="form-control" id="tickers" 
                   placeholder="Enter tickers separated by commas">
            <div class="form-text">For demo, try "AAPL" or "CRYPTO"</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="mb-3">
            <label for="strategyTypes" class="form-label">Strategy Types</label>
            <select class="form-select" id="strategyTypes" multiple>
              <option value="SMA" selected>SMA</option>
              <option value="EMA">EMA</option>
              <option value="MACD">MACD</option>
            </select>
          </div>
        </div>
        <div class="col-md-3">
          <div class="mb-3">
            <label for="direction" class="form-label">Direction</label>
            <select class="form-select" id="direction">
              <option value="Long" selected>Long</option>
              <option value="Short">Short</option>
              <option value="Both">Both</option>
            </select>
          </div>
        </div>
      </div>
      
      <div id="advancedConfig" class="d-none">
        <!-- Advanced configuration options -->
      </div>

      <div class="d-flex justify-content-between">
        <button type="button" class="btn btn-secondary" id="resetFormBtn">
          <i class="fas fa-undo me-1"></i> Reset
        </button>
        <button type="submit" class="btn btn-primary" id="runAnalysisBtn">
          <i class="fas fa-play me-1"></i> Run Analysis
        </button>
      </div>
    </form>
  </div>
</div>
```

Complementary JavaScript:

```javascript
document.addEventListener('DOMContentLoaded', function() {
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
});
```

This patterns guide provides concrete examples of how to implement UI components in context, ensuring consistency throughout the Sensylate application and making it easier to maintain and extend the interface in the future.
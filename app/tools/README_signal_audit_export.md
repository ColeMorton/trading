# Signal Audit Export Module

## Overview

The Signal Audit Export module provides functionality for exporting signal audit data to various formats, including CSV, JSON, HTML, and visualization capabilities. This module addresses the need for comprehensive analysis and reporting of signal audit data.

## Key Features

- **Multiple Export Formats**: Export to CSV, JSON, and HTML
- **Visualization Capabilities**: Generate charts and graphs for signal analysis
- **Dashboard Creation**: Create comprehensive dashboards for signal analysis
- **Backward Compatibility**: Convenience functions for seamless integration

## Usage

### Basic Usage

```python
from app.tools.signal_audit_export import SignalAuditExport
from app.tools.signal_conversion import SignalAudit

# Create a SignalAuditExport instance
exporter = SignalAuditExport(log)

# Export to CSV
exporter.export_to_csv(audit, "signal_audit.csv")

# Export to JSON
exporter.export_to_json(audit, "signal_audit.json")

# Export to HTML
exporter.export_to_html(audit, "signal_audit.html")

# Create a dashboard
exporter.create_dashboard(audit, "dashboard_dir", "strategy_id")
```

### CSV Export

CSV export provides a tabular representation of signal audit data:

```python
exporter.export_to_csv(
    audit,
    "signal_audit.csv",
    include_signals=True,
    include_conversions=True,
    include_rejections=True
)
```

### JSON Export

JSON export provides a structured representation of signal audit data:

```python
exporter.export_to_json(
    audit,
    "signal_audit.json",
    include_summary=True
)
```

### HTML Export

HTML export provides a formatted report with tables and visualizations:

```python
exporter.export_to_html(
    audit,
    "signal_audit.html",
    title="Signal Audit Report",
    include_visualizations=True
)
```

### Dashboard Creation

Dashboard creation provides a comprehensive analysis environment:

```python
exporter.create_dashboard(
    audit,
    "dashboard_dir",
    strategy_id="strategy",
    include_visualizations=True
)
```

### Convenience Function

For backward compatibility, a convenience function is provided:

```python
from app.tools.signal_audit_export import export_signal_audit

export_signal_audit(
    audit,
    "output_dir",
    strategy_id="strategy",
    formats=["csv", "json", "html", "dashboard"]
)
```

## Visualizations

The module provides several visualizations for signal analysis:

1. **Conversion Rate Pie Chart**: Shows the proportion of signals that were converted vs. rejected
2. **Signal Timeline**: Shows the sequence of signals, conversions, and rejections over time
3. **Rejection Reasons Bar Chart**: Shows the distribution of rejection reasons

## Dashboard Structure

The dashboard consists of the following components:

1. **Index Page**: Provides an overview and links to all exports
2. **HTML Report**: Provides a detailed report with tables and visualizations
3. **CSV Export**: Provides a tabular representation of signal audit data
4. **JSON Export**: Provides a structured representation of signal audit data

## Implementation Details

The module is implemented as a class-based design with the following components:

- **SignalAuditExport**: Main class for exporting signal audit data
- **export_to_csv**: Method for exporting to CSV
- **export_to_json**: Method for exporting to JSON
- **export_to_html**: Method for exporting to HTML
- **create_dashboard**: Method for creating a comprehensive dashboard
- **_create_visualizations_html**: Helper method for creating visualizations

## Benefits

1. **Comprehensive Analysis**: Multiple export formats for different analysis needs
2. **Visual Insights**: Visualizations provide intuitive understanding of signal behavior
3. **Shareable Reports**: HTML reports can be easily shared with stakeholders
4. **Integrated Dashboard**: Dashboard provides a unified view of signal audit data
5. **Extensible Design**: Easy to add new export formats or visualizations
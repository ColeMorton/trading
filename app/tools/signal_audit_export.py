"""
Signal Audit Trail Export Module.

This module provides functionality for exporting signal audit data to various formats,
including CSV, JSON, HTML, and visualization capabilities.
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List, Optional, Callable, Union
from pathlib import Path
import base64
from io import BytesIO
from datetime import datetime

from app.tools.signal_conversion import SignalAudit


class SignalAuditExport:
    """Class for exporting signal audit data to various formats."""
    
    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        """Initialize the SignalAuditExport class.
        
        Args:
            log: Logging function. If None, print statements will be used.
        """
        self.log = log if log is not None else self._default_log
    
    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging function that uses print statements.
        
        Args:
            message: Message to log
            level: Log level (info, warning, error, debug)
        """
        print(f"[{level.upper()}] {message}")
    
    def export_to_csv(
        self,
        audit: SignalAudit,
        filepath: str,
        include_signals: bool = True,
        include_conversions: bool = True,
        include_rejections: bool = True
    ) -> bool:
        """Export signal audit data to CSV.
        
        Args:
            audit: SignalAudit object containing audit data
            filepath: Path to save the CSV file
            include_signals: Whether to include signal data
            include_conversions: Whether to include conversion data
            include_rejections: Whether to include rejection data
            
        Returns:
            bool: True if export successful, False otherwise
        """
        try:
            # Convert audit data to DataFrame
            df = audit.to_dataframe()
            
            # Filter based on inclusion flags
            if not include_signals:
                df = df[df["event_type"] != "Signal"]
            if not include_conversions:
                df = df[df["event_type"] != "Conversion"]
            if not include_rejections:
                df = df[df["event_type"] != "Rejection"]
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            # Export to CSV
            df.to_csv(filepath, index=False)
            
            self.log(f"Signal audit data exported to CSV: {filepath}", "info")
            return True
        except Exception as e:
            self.log(f"Error exporting signal audit data to CSV: {str(e)}", "error")
            return False
    
    def export_to_json(
        self,
        audit: SignalAudit,
        filepath: str,
        include_summary: bool = True
    ) -> bool:
        """Export signal audit data to JSON.
        
        Args:
            audit: SignalAudit object containing audit data
            filepath: Path to save the JSON file
            include_summary: Whether to include summary statistics
            
        Returns:
            bool: True if export successful, False otherwise
        """
        try:
            # Convert audit data to DataFrame
            df = audit.to_dataframe()
            
            # Convert DataFrame to dict
            records = df.to_dict(orient="records")
            
            # Create export data
            export_data = {
                "signals": [s for s in records if s["event_type"] == "Signal"],
                "conversions": [c for c in records if c["event_type"] == "Conversion"],
                "rejections": [r for r in records if r["event_type"] == "Rejection"],
                "export_time": datetime.now().isoformat()
            }
            
            # Add summary if requested
            if include_summary:
                summary = audit.get_summary()
                export_data["summary"] = summary
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            # Export to JSON
            with open(filepath, "w") as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.log(f"Signal audit data exported to JSON: {filepath}", "info")
            return True
        except Exception as e:
            self.log(f"Error exporting signal audit data to JSON: {str(e)}", "error")
            return False
    
    def export_to_html(
        self,
        audit: SignalAudit,
        filepath: str,
        title: str = "Signal Audit Report",
        include_visualizations: bool = True
    ) -> bool:
        """Export signal audit data to HTML.
        
        Args:
            audit: SignalAudit object containing audit data
            filepath: Path to save the HTML file
            title: Title of the HTML report
            include_visualizations: Whether to include visualizations
            
        Returns:
            bool: True if export successful, False otherwise
        """
        try:
            # Convert audit data to DataFrame
            df = audit.to_dataframe()
            
            # Get summary statistics
            summary = audit.get_summary()
            
            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{title}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        line-height: 1.6;
                    }}
                    h1, h2, h3 {{
                        color: #333;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin-bottom: 20px;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    .summary-box {{
                        background-color: #f5f5f5;
                        border: 1px solid #ddd;
                        padding: 15px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }}
                    .metric {{
                        display: inline-block;
                        margin-right: 20px;
                        margin-bottom: 10px;
                    }}
                    .metric-value {{
                        font-weight: bold;
                        font-size: 1.2em;
                    }}
                    .visualization {{
                        margin: 20px 0;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <h1>{title}</h1>
                <p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h2>Summary</h2>
                <div class="summary-box">
                    <div class="metric">
                        <div>Total Signals</div>
                        <div class="metric-value">{summary['total_signals']}</div>
                    </div>
                    <div class="metric">
                        <div>Conversions</div>
                        <div class="metric-value">{summary['conversions']}</div>
                    </div>
                    <div class="metric">
                        <div>Rejections</div>
                        <div class="metric-value">{summary['rejections']}</div>
                    </div>
                    <div class="metric">
                        <div>Conversion Rate</div>
                        <div class="metric-value">{summary['conversion_rate']*100:.1f}%</div>
                    </div>
                </div>
            """
            
            # Add visualizations if requested
            if include_visualizations and len(df) > 0:
                # Create visualizations
                viz_html = self._create_visualizations_html(audit)
                html_content += viz_html
            
            # Add signal data table
            signals_df = df[df["event_type"] == "Signal"]
            if len(signals_df) > 0:
                html_content += """
                <h2>Signals</h2>
                <table>
                    <tr>
                        <th>Date</th>
                        <th>Value</th>
                        <th>Source</th>
                    </tr>
                """
                
                for _, row in signals_df.iterrows():
                    html_content += f"""
                    <tr>
                        <td>{row['date']}</td>
                        <td>{row['value']}</td>
                        <td>{row['source']}</td>
                    </tr>
                    """
                
                html_content += "</table>"
            
            # Add conversion data table
            conversions_df = df[df["event_type"] == "Conversion"]
            if len(conversions_df) > 0:
                html_content += """
                <h2>Conversions</h2>
                <table>
                    <tr>
                        <th>Date</th>
                        <th>Value</th>
                        <th>Reason</th>
                    </tr>
                """
                
                for _, row in conversions_df.iterrows():
                    html_content += f"""
                    <tr>
                        <td>{row['date']}</td>
                        <td>{row['value']}</td>
                        <td>{row['reason']}</td>
                    </tr>
                    """
                
                html_content += "</table>"
            
            # Add rejection data table
            rejections_df = df[df["event_type"] == "Rejection"]
            if len(rejections_df) > 0:
                html_content += """
                <h2>Rejections</h2>
                <table>
                    <tr>
                        <th>Date</th>
                        <th>Value</th>
                        <th>Reason</th>
                    </tr>
                """
                
                for _, row in rejections_df.iterrows():
                    html_content += f"""
                    <tr>
                        <td>{row['date']}</td>
                        <td>{row['value']}</td>
                        <td>{row['reason']}</td>
                    </tr>
                    """
                
                html_content += "</table>"
            
            # Close HTML
            html_content += """
            </body>
            </html>
            """
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            # Export to HTML
            with open(filepath, "w") as f:
                f.write(html_content)
            
            self.log(f"Signal audit data exported to HTML: {filepath}", "info")
            return True
        except Exception as e:
            self.log(f"Error exporting signal audit data to HTML: {str(e)}", "error")
            return False
    
    def _create_visualizations_html(self, audit: SignalAudit) -> str:
        """Create HTML content for visualizations.
        
        Args:
            audit: SignalAudit object containing audit data
            
        Returns:
            str: HTML content for visualizations
        """
        try:
            # Convert audit data to DataFrame
            df = audit.to_dataframe()
            
            # Get summary statistics
            summary = audit.get_summary()
            
            # Create HTML content for visualizations
            html_content = "<h2>Visualizations</h2>"
            
            # 1. Conversion Rate Pie Chart
            fig, ax = plt.subplots(figsize=(8, 6))
            labels = ['Converted', 'Rejected']
            sizes = [summary['conversions'], summary['rejections']]
            colors = ['#4CAF50', '#F44336']
            
            if sum(sizes) > 0:  # Only create pie chart if there are signals
                ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax.axis('equal')
                plt.title('Signal Conversion Rate')
                
                # Convert plot to base64 for embedding in HTML
                buffer = BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                img_str = base64.b64encode(buffer.read()).decode('utf-8')
                plt.close()
                
                html_content += f"""
                <div class="visualization">
                    <h3>Signal Conversion Rate</h3>
                    <img src="data:image/png;base64,{img_str}" alt="Conversion Rate Pie Chart">
                </div>
                """
            
            # 2. Signal Timeline
            if len(df) > 0:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Create a new column for plotting
                df['plot_value'] = 0
                df.loc[df['event_type'] == 'Signal', 'plot_value'] = 1
                df.loc[df['event_type'] == 'Conversion', 'plot_value'] = 2
                df.loc[df['event_type'] == 'Rejection', 'plot_value'] = 3
                
                # Plot events
                for event_type, color, marker in [
                    ('Signal', '#2196F3', 'o'),
                    ('Conversion', '#4CAF50', '^'),
                    ('Rejection', '#F44336', 'x')
                ]:
                    event_df = df[df['event_type'] == event_type]
                    if len(event_df) > 0:
                        ax.scatter(
                            event_df['date'],
                            event_df['plot_value'],
                            color=color,
                            marker=marker,
                            label=event_type,
                            s=100
                        )
                
                # Set labels and title
                ax.set_yticks([1, 2, 3])
                ax.set_yticklabels(['Signal', 'Conversion', 'Rejection'])
                ax.set_xlabel('Date')
                ax.set_title('Signal Audit Timeline')
                ax.legend()
                
                # Format x-axis dates
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Convert plot to base64 for embedding in HTML
                buffer = BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                img_str = base64.b64encode(buffer.read()).decode('utf-8')
                plt.close()
                
                html_content += f"""
                <div class="visualization">
                    <h3>Signal Audit Timeline</h3>
                    <img src="data:image/png;base64,{img_str}" alt="Signal Audit Timeline">
                </div>
                """
            
            # 3. Rejection Reasons Bar Chart
            rejection_reasons = summary.get('rejection_reasons', {})
            if rejection_reasons:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                reasons = list(rejection_reasons.keys())
                counts = list(rejection_reasons.values())
                
                # Sort by count
                sorted_indices = np.argsort(counts)
                reasons = [reasons[i] for i in sorted_indices]
                counts = [counts[i] for i in sorted_indices]
                
                # Create bar chart
                ax.barh(reasons, counts, color='#F44336')
                ax.set_xlabel('Count')
                ax.set_ylabel('Reason')
                ax.set_title('Signal Rejection Reasons')
                
                # Add count labels
                for i, count in enumerate(counts):
                    ax.text(count + 0.1, i, str(count), va='center')
                
                plt.tight_layout()
                
                # Convert plot to base64 for embedding in HTML
                buffer = BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                img_str = base64.b64encode(buffer.read()).decode('utf-8')
                plt.close()
                
                html_content += f"""
                <div class="visualization">
                    <h3>Signal Rejection Reasons</h3>
                    <img src="data:image/png;base64,{img_str}" alt="Signal Rejection Reasons">
                </div>
                """
            
            return html_content
        except Exception as e:
            self.log(f"Error creating visualizations: {str(e)}", "error")
            return "<p>Error creating visualizations</p>"
    
    def create_dashboard(
        self,
        audit: SignalAudit,
        output_dir: str,
        strategy_id: str = "strategy",
        include_visualizations: bool = True
    ) -> bool:
        """Create a comprehensive dashboard for signal analysis.
        
        Args:
            audit: SignalAudit object containing audit data
            output_dir: Directory to save dashboard files
            strategy_id: Strategy identifier for file naming
            include_visualizations: Whether to include visualizations
            
        Returns:
            bool: True if dashboard creation successful, False otherwise
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Export to various formats
            csv_path = os.path.join(output_dir, f"{strategy_id}_signal_audit.csv")
            json_path = os.path.join(output_dir, f"{strategy_id}_signal_audit.json")
            html_path = os.path.join(output_dir, f"{strategy_id}_signal_audit.html")
            
            # Export to each format
            csv_success = self.export_to_csv(audit, csv_path)
            json_success = self.export_to_json(audit, json_path)
            html_success = self.export_to_html(
                audit,
                html_path,
                title=f"{strategy_id} Signal Audit Report",
                include_visualizations=include_visualizations
            )
            
            # Create index.html that links to all exports
            index_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{strategy_id} Signal Audit Dashboard</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        line-height: 1.6;
                    }}
                    h1, h2 {{
                        color: #333;
                    }}
                    .dashboard-links {{
                        margin: 20px 0;
                    }}
                    .dashboard-link {{
                        display: inline-block;
                        margin-right: 20px;
                        padding: 10px 15px;
                        background-color: #4CAF50;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                    }}
                    .dashboard-link:hover {{
                        background-color: #45a049;
                    }}
                    .summary-box {{
                        background-color: #f5f5f5;
                        border: 1px solid #ddd;
                        padding: 15px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }}
                    .metric {{
                        display: inline-block;
                        margin-right: 20px;
                        margin-bottom: 10px;
                    }}
                    .metric-value {{
                        font-weight: bold;
                        font-size: 1.2em;
                    }}
                </style>
            </head>
            <body>
                <h1>{strategy_id} Signal Audit Dashboard</h1>
                <p>Dashboard generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="dashboard-links">
                    <a class="dashboard-link" href="{os.path.basename(html_path)}">HTML Report</a>
                    <a class="dashboard-link" href="{os.path.basename(csv_path)}">CSV Export</a>
                    <a class="dashboard-link" href="{os.path.basename(json_path)}">JSON Export</a>
                </div>
                
                <h2>Summary</h2>
                <div class="summary-box">
            """
            
            # Add summary statistics
            summary = audit.get_summary()
            index_html += f"""
                    <div class="metric">
                        <div>Total Signals</div>
                        <div class="metric-value">{summary['total_signals']}</div>
                    </div>
                    <div class="metric">
                        <div>Conversions</div>
                        <div class="metric-value">{summary['conversions']}</div>
                    </div>
                    <div class="metric">
                        <div>Rejections</div>
                        <div class="metric-value">{summary['rejections']}</div>
                    </div>
                    <div class="metric">
                        <div>Conversion Rate</div>
                        <div class="metric-value">{summary['conversion_rate']*100:.1f}%</div>
                    </div>
                </div>
            """
            
            # Close HTML
            index_html += """
            </body>
            </html>
            """
            
            # Write index.html
            index_path = os.path.join(output_dir, "index.html")
            with open(index_path, "w") as f:
                f.write(index_html)
            
            self.log(f"Signal audit dashboard created in {output_dir}", "info")
            return csv_success and json_success and html_success
        except Exception as e:
            self.log(f"Error creating signal audit dashboard: {str(e)}", "error")
            return False


# Convenience function for backward compatibility
def export_signal_audit(
    audit: SignalAudit,
    output_dir: str,
    strategy_id: str = "strategy",
    formats: List[str] = ["csv", "json", "html"],
    log: Optional[Callable[[str, str], None]] = None
) -> bool:
    """Export signal audit data to various formats.
    
    Args:
        audit: SignalAudit object containing audit data
        output_dir: Directory to save export files
        strategy_id: Strategy identifier for file naming
        formats: List of formats to export to (csv, json, html)
        log: Logging function
        
    Returns:
        bool: True if export successful, False otherwise
    """
    exporter = SignalAuditExport(log)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    success = True
    
    # Export to each requested format
    if "csv" in formats:
        csv_path = os.path.join(output_dir, f"{strategy_id}_signal_audit.csv")
        success = success and exporter.export_to_csv(audit, csv_path)
    
    if "json" in formats:
        json_path = os.path.join(output_dir, f"{strategy_id}_signal_audit.json")
        success = success and exporter.export_to_json(audit, json_path)
    
    if "html" in formats:
        html_path = os.path.join(output_dir, f"{strategy_id}_signal_audit.html")
        success = success and exporter.export_to_html(
            audit,
            html_path,
            title=f"{strategy_id} Signal Audit Report"
        )
    
    if "dashboard" in formats:
        success = success and exporter.create_dashboard(audit, output_dir, strategy_id)
    
    return success
"""
Tests for the signal audit export module.
"""

import unittest
import os
import json
import tempfile
import pandas as pd
from datetime import datetime, timedelta
from app.tools.signal_conversion import SignalAudit
from app.tools.signal_audit_export import SignalAuditExport, export_signal_audit


class TestSignalAuditExport(unittest.TestCase):
    """Test cases for the SignalAuditExport class."""
    
    def setUp(self):
        """Set up test data."""
        # Create a SignalAudit instance with test data
        self.audit = SignalAudit()
        
        # Add signals
        for i in range(5):
            self.audit.add_signal(
                date=datetime(2023, 1, i+1),
                value=1 if i % 2 == 0 else -1,
                source="Test Source"
            )
        
        # Add conversions
        for i in range(3):
            self.audit.add_conversion(
                date=datetime(2023, 1, i+2),
                signal_value=1 if i % 2 == 0 else -1,
                position_value=1 if i % 2 == 0 else -1,
                reason="Test Conversion"
            )
        
        # Add rejections
        for i in range(2):
            self.audit.add_rejection(
                date=datetime(2023, 1, i+4),
                signal_value=1 if i % 2 == 0 else -1,
                reason="Test Rejection"
            )
        
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        
        # Create exporter
        self.exporter = SignalAuditExport()
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary files
        for filename in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, filename))
        
        # Remove temporary directory
        os.rmdir(self.temp_dir)
    
    def test_export_to_csv(self):
        """Test exporting signal audit data to CSV."""
        # Define output path
        csv_path = os.path.join(self.temp_dir, "test_audit.csv")
        
        # Export to CSV
        result = self.exporter.export_to_csv(self.audit, csv_path)
        
        # Verify export was successful
        self.assertTrue(result)
        self.assertTrue(os.path.exists(csv_path))
        
        # Read CSV and verify content
        df = pd.read_csv(csv_path)
        
        # Verify all events are included
        self.assertEqual(len(df), 10)  # 5 signals + 3 conversions + 2 rejections
        
        # Verify event types
        self.assertEqual(len(df[df["event_type"] == "Signal"]), 5)
        self.assertEqual(len(df[df["event_type"] == "Conversion"]), 3)
        self.assertEqual(len(df[df["event_type"] == "Rejection"]), 2)
    
    def test_export_to_json(self):
        """Test exporting signal audit data to JSON."""
        # Define output path
        json_path = os.path.join(self.temp_dir, "test_audit.json")
        
        # Export to JSON
        result = self.exporter.export_to_json(self.audit, json_path)
        
        # Verify export was successful
        self.assertTrue(result)
        self.assertTrue(os.path.exists(json_path))
        
        # Read JSON and verify content
        with open(json_path, "r") as f:
            data = json.load(f)
        
        # Verify all events are included
        self.assertEqual(len(data["signals"]), 5)
        self.assertEqual(len(data["conversions"]), 3)
        self.assertEqual(len(data["rejections"]), 2)
        
        # Verify summary is included
        self.assertIn("summary", data)
        self.assertEqual(data["summary"]["total_signals"], 5)
        self.assertEqual(data["summary"]["conversions"], 3)
        self.assertEqual(data["summary"]["rejections"], 2)
    
    def test_export_to_html(self):
        """Test exporting signal audit data to HTML."""
        # Define output path
        html_path = os.path.join(self.temp_dir, "test_audit.html")
        
        # Export to HTML
        result = self.exporter.export_to_html(self.audit, html_path)
        
        # Verify export was successful
        self.assertTrue(result)
        self.assertTrue(os.path.exists(html_path))
        
        # Read HTML and verify content
        with open(html_path, "r") as f:
            html_content = f.read()
        
        # Verify basic HTML structure
        self.assertIn("<!DOCTYPE html>", html_content)
        self.assertIn("<html>", html_content)
        self.assertIn("</html>", html_content)
        
        # Verify summary section
        self.assertIn("<h2>Summary</h2>", html_content)
        self.assertIn("Total Signals", html_content)
        self.assertIn("Conversions", html_content)
        self.assertIn("Rejections", html_content)
        
        # Verify tables
        self.assertIn("<h2>Signals</h2>", html_content)
        self.assertIn("<h2>Conversions</h2>", html_content)
        self.assertIn("<h2>Rejections</h2>", html_content)
    
    def test_create_dashboard(self):
        """Test creating a comprehensive dashboard."""
        # Export dashboard
        result = self.exporter.create_dashboard(
            self.audit,
            self.temp_dir,
            "test_strategy"
        )
        
        # Verify export was successful
        self.assertTrue(result)
        
        # Verify all files were created
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "index.html")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "test_strategy_signal_audit.csv")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "test_strategy_signal_audit.json")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "test_strategy_signal_audit.html")))
    
    def test_convenience_function(self):
        """Test the convenience function for backward compatibility."""
        # Export using convenience function
        result = export_signal_audit(
            self.audit,
            self.temp_dir,
            "test_strategy",
            formats=["csv", "json", "html"]
        )
        
        # Verify export was successful
        self.assertTrue(result)
        
        # Verify all files were created
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "test_strategy_signal_audit.csv")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "test_strategy_signal_audit.json")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "test_strategy_signal_audit.html")))


if __name__ == "__main__":
    unittest.main()
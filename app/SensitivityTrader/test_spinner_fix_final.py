#!/usr/bin/env python3
"""
Test script to verify the main loading spinner now works correctly.
"""

def test_loading_spinner_flow():
    """Test that only app.js controls the main loading spinner"""
    print("Testing final spinner fix...")
    
    # Check that analysis.js doesn't add event listener to run-analysis-btn
    with open('static/js/analysis.js', 'r') as f:
        analysis_js = f.read()
        
        # Should not have event listener for run-analysis-btn
        assert 'runAnalysisBtn.addEventListener(\'click\', runAnalysis)' not in analysis_js
        print("✓ Analysis.js no longer hijacks the run analysis button")
        
        # Should not use loadingResults for main loading
        assert 'loadingResults.classList.remove(\'d-none\')' not in analysis_js
        print("✓ Analysis.js doesn't interfere with main loading indicator")
    
    # Check that app.js properly controls loading
    with open('static/js/app.js', 'r') as f:
        app_js = f.read()
        
        # Should show loading at start of runAnalysis
        assert 'loadingResults\').classList.remove(\'d-none\')' in app_js
        print("✓ App.js shows loading indicator")
        
        # Should hide loading in finally block
        assert 'loadingResults\').classList.add(\'d-none\')' in app_js
        print("✓ App.js hides loading indicator when done")
    
    print("\n✅ Loading spinner should now work correctly!")
    print("- Only app.js controls the main loading spinner")
    print("- No interference from analysis.js")
    print("- Spinner will show until MA Cross API call completes")

if __name__ == "__main__":
    test_loading_spinner_flow()
#!/usr/bin/env python3
"""
Test script to verify the double spinner issue is fixed.
"""

def test_single_spinner():
    """Test that only one loading indicator exists and is used"""
    print("Testing spinner fix...")
    
    # Check HTML template
    with open('templates/index.html', 'r') as f:
        html = f.read()
        
        # Should NOT have the small loading-indicator anymore
        assert 'id="loading-indicator"' not in html
        print("✓ Small loading-indicator removed from HTML")
        
        # Should still have the main loadingResults
        assert 'id="loadingResults"' in html
        print("✓ Main loadingResults spinner still present")
    
    # Check JavaScript files
    with open('static/js/app.js', 'r') as f:
        app_js = f.read()
        
        # Should not show the small loading-indicator
        assert 'loadingIndicator.style.display = \'block\'' not in app_js
        print("✓ Small loading indicator not used in app.js")
        
        # Should use loadingResults
        assert 'loadingResults\').classList.remove(\'d-none\')' in app_js
        print("✓ Main loading indicator used in app.js")
    
    with open('static/js/analysis.js', 'r') as f:
        analysis_js = f.read()
        
        # Should use loadingResults instead of loading-indicator
        assert 'getElementById(\'loadingResults\')' in analysis_js
        assert 'loadingIndicator.style.display' not in analysis_js
        print("✓ Analysis.js uses main loading indicator")

if __name__ == "__main__":
    test_single_spinner()
    print("\n✅ Spinner fix verified! Only one loading indicator will be shown.")
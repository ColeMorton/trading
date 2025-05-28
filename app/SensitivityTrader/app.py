import os
import json
import logging
import pandas as pd
from flask import Flask, render_template, request, jsonify, session, send_file
from pathlib import Path
from data_processor import DataProcessor
from models import PortfolioModel
from services.analysis_service import AnalysisService

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "sensylate_secret_key")

# Initialize data processor and analysis service
data_processor = DataProcessor()
analysis_service = AnalysisService()

# Default configuration
DEFAULT_CONFIG = {
    "WINDOWS": 89,
    "REFRESH": True,
    "STRATEGY_TYPES": ["SMA", "EMA"],
    "DIRECTION": "Long",
    "USE_HOURLY": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "USE_SYNTHETIC": False,
    "TICKER_2": "",
    "USE_CURRENT": True,
    "USE_SCANNER": False,
    "MINIMUMS": {
        "WIN_RATE": 0.44,
        "TRADES": 54,
        "EXPECTANCY_PER_TRADE": 1,
        "PROFIT_FACTOR": 1,
        "SORTINO_RATIO": 0.4,
    },
    "SORT_BY": "Score",
    "SORT_ASC": False,
    "USE_GBM": False
}

@app.route('/')
def index():
    """Render the main application page."""
    if 'portfolio' not in session:
        session['portfolio'] = []
    return render_template('index.html', default_config=json.dumps(DEFAULT_CONFIG))

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Process the parameter sensitivity analysis request."""
    try:
        data = request.json
        tickers = data.get('tickers', '')
        config = data.get('config', DEFAULT_CONFIG)
        
        logger.debug(f"Received analysis request for tickers: {tickers}")
        
        # Use the analysis service to run the analysis
        result = analysis_service.run_analysis(tickers, config)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/sample_data', methods=['GET'])
def sample_data():
    """Provide sample data for demonstration - disabled to prevent automatic loading."""
    # Return empty results to prevent loading mock data
    return jsonify({'status': 'success', 'results': []})

@app.route('/api/portfolio', methods=['GET', 'POST', 'DELETE'])
def portfolio():
    """Manage the user's custom portfolio."""
    if request.method == 'GET':
        # Get the current portfolio
        portfolio_items = session.get('portfolio', [])
        return jsonify({'status': 'success', 'portfolio': portfolio_items})
    
    elif request.method == 'POST':
        # Add item to portfolio
        try:
            item = request.json
            current_portfolio = session.get('portfolio', [])
            
            # Check if item already exists in portfolio
            exists = False
            for i, existing_item in enumerate(current_portfolio):
                if (existing_item['Ticker'] == item['Ticker'] and 
                    existing_item['Strategy Type'] == item['Strategy Type'] and
                    existing_item['Short Window'] == item['Short Window'] and
                    existing_item['Long Window'] == item['Long Window']):
                    exists = True
                    # Update weight if it exists
                    current_portfolio[i]['weight'] = item.get('weight', current_portfolio[i].get('weight', 1))
                    break
            
            if not exists:
                item['weight'] = item.get('weight', 1)  # Default weight
                current_portfolio.append(item)
            
            session['portfolio'] = current_portfolio
            return jsonify({'status': 'success', 'portfolio': current_portfolio})
        
        except Exception as e:
            logger.error(f"Error adding to portfolio: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    elif request.method == 'DELETE':
        # Remove item from portfolio
        try:
            item = request.json
            current_portfolio = session.get('portfolio', [])
            
            new_portfolio = [
                p for p in current_portfolio 
                if not (p['Ticker'] == item['Ticker'] and 
                       p['Strategy Type'] == item['Strategy Type'] and
                       p['Short Window'] == item['Short Window'] and
                       p['Long Window'] == item['Long Window'])
            ]
            
            session['portfolio'] = new_portfolio
            return jsonify({'status': 'success', 'portfolio': new_portfolio})
        
        except Exception as e:
            logger.error(f"Error removing from portfolio: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/portfolio/clear', methods=['POST'])
def clear_portfolio():
    """Clear the entire portfolio."""
    session['portfolio'] = []
    return jsonify({'status': 'success', 'portfolio': []})

@app.route('/api/portfolio/analyze', methods=['POST'])
def analyze_portfolio():
    """Analyze the current portfolio."""
    try:
        portfolio_items = session.get('portfolio', [])
        if not portfolio_items:
            return jsonify({'status': 'error', 'message': 'Portfolio is empty'}), 400
        
        # Create a portfolio model and analyze it
        portfolio_model = PortfolioModel(portfolio_items)
        analysis_results = portfolio_model.analyze()
        
        return jsonify({'status': 'success', 'analysis': analysis_results})
    
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Helper function to get project root
def get_project_root():
    """Get the project root directory."""
    # Go up two levels from the current file (app/SensitivityTrader -> app -> trading)
    return str(Path(__file__).parent.parent.parent)

@app.route('/api/csv/<path:filename>', methods=['GET'])
def get_csv_file(filename):
    """Serve a CSV file."""
    try:
        # Ensure the filename is safe and within the csv directory
        base_dir = os.path.join(get_project_root(), 'csv')
        file_path = os.path.normpath(os.path.join(base_dir, filename))
        
        # Security check: ensure the file is within the csv directory
        if not file_path.startswith(base_dir):
            return jsonify({'status': 'error', 'message': 'Invalid file path'}), 403
        
        # Check if the file exists
        if not os.path.isfile(file_path):
            return jsonify({'status': 'error', 'message': 'File not found'}), 404
        
        # Serve the file
        return send_file(file_path, mimetype='text/csv', as_attachment=True)
    except Exception as e:
        logger.error(f"Error serving CSV file: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

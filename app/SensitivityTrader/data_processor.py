import os
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """Handles data processing for the Sensylate application."""
    
    def __init__(self):
        """Initialize the data processor."""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'attached_assets')
        
    def load_sample_data(self, filename):
        """Load sample data from CSV files."""
        try:
            file_path = os.path.join(self.data_dir, filename)
            logger.debug(f"Attempting to load data from {file_path}")
            
            if not os.path.exists(file_path):
                # For testing, look in the attached_assets directory
                file_path = os.path.join('attached_assets', filename)
                logger.debug(f"Attempting alternate path: {file_path}")
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {filename}")
                return []
            
            df = pd.read_csv(file_path)
            
            # Convert DataFrame to list of records
            records = df.to_dict('records')
            
            # Convert NumPy numeric types to Python native types for JSON serialization
            for record in records:
                for key, value in record.items():
                    if isinstance(value, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64, 
                                         np.uint8, np.uint16, np.uint32, np.uint64)):
                        record[key] = int(value)
                    elif isinstance(value, (np.float_, np.float16, np.float32, np.float64)):
                        record[key] = float(value)
                    elif pd.isna(value):
                        record[key] = None
            
            logger.debug(f"Successfully loaded {len(records)} records from {filename}")
            return records
        
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def analyze_tickers(self, tickers, config):
        """Analyze the provided tickers with the given configuration.
        
        In a production environment, this would implement the actual parameter
        sensitivity testing logic. For demonstration purposes, we'll use sample data.
        """
        logger.debug(f"Analyzing tickers: {tickers} with config: {config}")
        
        tickers_list = [t.strip() for t in tickers.split(',')]
        
        # For demonstration, we'll use the sample data
        if any('CRYPTO' in t.upper() for t in tickers_list):
            results = self.load_sample_data('DAILY_crypto.csv')
        else:
            results = self.load_sample_data('AAPL_D_SMA.csv')
        
        # Apply filtering based on minimums
        filtered_results = self._apply_filters(results, config)
        
        # Sort results
        sorted_results = self._sort_results(filtered_results, config)
        
        return sorted_results
    
    def _apply_filters(self, results, config):
        """Apply filters based on the configuration minimums."""
        minimums = config.get('MINIMUMS', {})
        
        filtered = []
        for record in results:
            # Check all minimum criteria
            passes = True
            
            # Win Rate check
            if 'Win Rate [%]' in record and minimums.get('WIN_RATE'):
                win_rate = record['Win Rate [%]'] / 100  # Convert from percentage to decimal
                if win_rate < minimums['WIN_RATE']:
                    passes = False
            
            # Trades check
            if 'Total Trades' in record and minimums.get('TRADES'):
                if record['Total Trades'] < minimums['TRADES']:
                    passes = False
            
            # Expectancy per Trade check
            if 'Expectancy per Trade' in record and minimums.get('EXPECTANCY_PER_TRADE'):
                if record['Expectancy per Trade'] < minimums['EXPECTANCY_PER_TRADE']:
                    passes = False
            
            # Profit Factor check
            if 'Profit Factor' in record and minimums.get('PROFIT_FACTOR'):
                if record['Profit Factor'] < minimums['PROFIT_FACTOR']:
                    passes = False
            
            # Sortino Ratio check
            if 'Sortino Ratio' in record and minimums.get('SORTINO_RATIO'):
                if record['Sortino Ratio'] < minimums['SORTINO_RATIO']:
                    passes = False
            
            if passes:
                filtered.append(record)
        
        return filtered
    
    def _sort_results(self, results, config):
        """Sort results based on the configuration."""
        sort_by = config.get('SORT_BY', 'Score')
        sort_asc = config.get('SORT_ASC', False)
        
        # If sort_by column is missing, default to the first column
        if results and sort_by not in results[0]:
            sort_by = list(results[0].keys())[0]
        
        # Sort the results
        sorted_results = sorted(
            results,
            key=lambda x: (x.get(sort_by, 0) if x.get(sort_by) is not None else 0),
            reverse=not sort_asc
        )
        
        return sorted_results

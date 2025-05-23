import logging
from typing import Dict, Any, Optional

from interfaces.analysis_service import IAnalysisService
from interfaces.analysis_adapter import IAnalysisAdapter
from adapters.ma_cross_adapter import MACrossAdapter
from exceptions.analysis_exceptions import AnalysisError

logger = logging.getLogger(__name__)

class AnalysisService(IAnalysisService):
    """Service for running analysis and managing results."""
    
    def __init__(self, adapter: Optional[IAnalysisAdapter] = None):
        """
        Initialize the analysis service.
        
        Args:
            adapter: Analysis adapter implementation
        """
        self.adapter = adapter if adapter is not None else MACrossAdapter()
    
    def run_analysis(self, tickers: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run analysis with the provided tickers and configuration.
        
        Args:
            tickers: Comma-separated list of tickers
            config: Configuration for the analysis
            
        Returns:
            Dictionary containing analysis results, CSV file metadata, and status
        """
        try:
            # Add tickers to the configuration
            config['tickers'] = tickers
            
            logger.info(f"Starting analysis for tickers: {tickers}")
            
            # Run the analysis
            result = self.adapter.run_analysis(config)
            
            # Extract portfolios and CSV files from the result
            portfolios = result.get("portfolios", [])
            csv_files = result.get("csv_files", [])
            logs = result.get("logs", [])
            
            # Return the results
            if portfolios:
                return {
                    'status': 'success',
                    'results': portfolios,
                    'csv_files': csv_files,
                    'logs': logs,
                    'message': f"Analysis completed successfully with {len(portfolios)} results and {len(csv_files)} CSV files"
                }
            else:
                return {
                    'status': 'success',
                    'results': [],
                    'csv_files': csv_files,
                    'logs': logs,
                    'message': "Analysis completed but no results matched the criteria"
                }
        
        except AnalysisError as e:
            logger.error(f"Analysis error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                'status': 'error',
                'message': f"An unexpected error occurred: {str(e)}"
            }
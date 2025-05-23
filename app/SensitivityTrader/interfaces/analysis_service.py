from abc import ABC, abstractmethod
from typing import Dict, Any

class IAnalysisService(ABC):
    """Interface for analysis services."""
    
    @abstractmethod
    def run_analysis(self, tickers: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run analysis with the provided tickers and configuration.
        
        Args:
            tickers: Comma-separated list of tickers
            config: Configuration for the analysis
            
        Returns:
            Dictionary containing analysis results and status
        """
        pass
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class IAnalysisAdapter(ABC):
    """Interface for analysis adapters."""
    
    @abstractmethod
    def run_analysis(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run analysis with the provided configuration.
        
        Args:
            config: Configuration for the analysis
            
        Returns:
            Dictionary containing analysis results, CSV file metadata, and logs
        """
        pass
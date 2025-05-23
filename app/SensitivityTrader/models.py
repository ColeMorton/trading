import logging
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

class PortfolioModel:
    """Model for portfolio analysis and management."""
    
    def __init__(self, portfolio_items):
        """Initialize the portfolio model with portfolio items."""
        self.portfolio_items = portfolio_items
    
    def analyze(self):
        """Analyze the portfolio performance and characteristics."""
        if not self.portfolio_items:
            return {
                'error': 'Portfolio is empty'
            }
        
        try:
            # Calculate aggregate metrics
            total_weight = sum(item.get('weight', 1) for item in self.portfolio_items)
            
            # Normalize weights to ensure they sum to 1
            normalized_weights = [item.get('weight', 1) / total_weight for item in self.portfolio_items]
            
            # Calculate weighted metrics
            weighted_metrics = {
                'win_rate': 0,
                'expectancy': 0,
                'profit_factor': 0,
                'sortino_ratio': 0,
                'total_return': 0,
                'max_drawdown': 0
            }
            
            for i, item in enumerate(self.portfolio_items):
                weight = normalized_weights[i]
                
                # Win Rate
                if 'Win Rate [%]' in item:
                    weighted_metrics['win_rate'] += (item['Win Rate [%]'] / 100) * weight
                
                # Expectancy per Trade
                if 'Expectancy per Trade' in item:
                    weighted_metrics['expectancy'] += item['Expectancy per Trade'] * weight
                
                # Profit Factor
                if 'Profit Factor' in item:
                    weighted_metrics['profit_factor'] += item['Profit Factor'] * weight
                
                # Sortino Ratio
                if 'Sortino Ratio' in item:
                    weighted_metrics['sortino_ratio'] += item['Sortino Ratio'] * weight
                
                # Total Return
                if 'Total Return [%]' in item:
                    weighted_metrics['total_return'] += item['Total Return [%]'] * weight
                
                # Max Drawdown
                if 'Max Drawdown [%]' in item:
                    # We use a weighted average for drawdown as a simplification
                    # In reality, portfolio drawdown would need time-series data
                    weighted_metrics['max_drawdown'] += item['Max Drawdown [%]'] * weight
            
            # Calculate diversity metrics
            tickers = [item['Ticker'] for item in self.portfolio_items]
            unique_tickers = len(set(tickers))
            ticker_counts = defaultdict(int)
            for ticker in tickers:
                ticker_counts[ticker] += 1
            
            strategy_types = [item['Strategy Type'] for item in self.portfolio_items]
            unique_strategies = len(set(strategy_types))
            
            # Format metrics for display
            formatted_metrics = {
                'win_rate': f"{weighted_metrics['win_rate'] * 100:.2f}%",
                'expectancy': f"{weighted_metrics['expectancy']:.2f}",
                'profit_factor': f"{weighted_metrics['profit_factor']:.2f}",
                'sortino_ratio': f"{weighted_metrics['sortino_ratio']:.2f}",
                'total_return': f"{weighted_metrics['total_return']:.2f}%",
                'max_drawdown': f"{weighted_metrics['max_drawdown']:.2f}%",
                'ticker_diversity': f"{unique_tickers} unique out of {len(tickers)} total",
                'strategy_diversity': f"{unique_strategies} unique strategies",
                'most_common_ticker': max(ticker_counts.items(), key=lambda x: x[1])[0] if ticker_counts else "None"
            }
            
            # Raw metrics for calculations
            raw_metrics = {
                'win_rate': weighted_metrics['win_rate'],
                'expectancy': weighted_metrics['expectancy'],
                'profit_factor': weighted_metrics['profit_factor'],
                'sortino_ratio': weighted_metrics['sortino_ratio'],
                'total_return': weighted_metrics['total_return'],
                'max_drawdown': weighted_metrics['max_drawdown'],
                'ticker_counts': dict(ticker_counts),
                'unique_tickers': unique_tickers,
                'unique_strategies': unique_strategies
            }
            
            # Calculate a portfolio score
            # This is a simplified calculation that weighs various metrics
            score_components = {
                'win_rate': weighted_metrics['win_rate'] * 20,  # Scale 0-1 to 0-20
                'expectancy': min(weighted_metrics['expectancy'] / 10, 1) * 20,  # Cap at 20
                'profit_factor': min(weighted_metrics['profit_factor'] / 5, 1) * 20,  # Cap at 20
                'sortino_ratio': min(weighted_metrics['sortino_ratio'] / 3, 1) * 20,  # Cap at 20
                'drawdown_protection': (1 - min(weighted_metrics['max_drawdown'] / 100, 1)) * 20,  # Inverse, cap at 20
            }
            
            portfolio_score = sum(score_components.values())
            
            return {
                'formatted': formatted_metrics,
                'raw': raw_metrics,
                'score': f"{portfolio_score:.2f}/100",
                'score_components': score_components
            }
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {str(e)}")
            return {
                'error': f"Analysis failed: {str(e)}"
            }

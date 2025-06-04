/**
 * Test suite for metric_type handling in ResultsTable component.
 *
 * Tests the component to ensure metric_type is properly displayed
 * in expandable row details with correct formatting and badges.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ResultsTable from '../ResultsTable';
import { AnalysisResult } from '../../types';

// Mock Icon component
jest.mock('../Icon', () => {
  return function MockIcon({ icon, size, className }: { icon: string; size?: string; className?: string }) {
    return (
      <span
        className={`mock-icon ${className || ''}`}
        data-icon={icon}
        data-size={size}
      />
    );
  };
});

// Mock icons
jest.mock('../../utils/icons', () => ({
  icons: {
    chevronRight: 'chevron-right',
    chevronDown: 'chevron-down',
    table: 'table',
    download: 'download',
    search: 'search',
    sort: 'sort',
    sortUp: 'sort-up',
    sortDown: 'sort-down',
    warning: 'warning',
    brand: 'brand',
  },
}));

describe('ResultsTable metric_type handling', () => {
  const sampleResultWithMetricType: AnalysisResult = {
    ticker: 'BTC-USD',
    strategy_type: 'EMA',
    short_window: 5,
    long_window: 10,
    signal_window: 0,
    direction: 'Long',
    timeframe: 'D',
    total_trades: 50,
    win_rate: 0.6,
    profit_factor: 2.0,
    expectancy_per_trade: 500.0,
    sortino_ratio: 1.5,
    max_drawdown: 20.0,
    total_return: 150.0,
    annual_return: 25.0,
    sharpe_ratio: 1.2,
    winning_trades: 30,
    losing_trades: 20,
    score: 1.0,
    beats_bnh: 10.0,
    has_open_trade: false,
    has_signal_entry: true,
    metric_type: 'Most Sharpe Ratio, Most Total Return [%]',
  };

  const sampleResultWithoutMetricType: AnalysisResult = {
    ticker: 'ETH-USD',
    strategy_type: 'SMA',
    short_window: 12,
    long_window: 26,
    signal_window: 0,
    direction: 'Long',
    timeframe: 'D',
    total_trades: 30,
    win_rate: 0.7,
    profit_factor: 1.8,
    expectancy_per_trade: 300.0,
    sortino_ratio: 1.2,
    max_drawdown: 15.0,
    total_return: 100.0,
    annual_return: 20.0,
    sharpe_ratio: 1.0,
    winning_trades: 21,
    losing_trades: 9,
    score: 0.9,
    beats_bnh: 5.0,
    has_open_trade: true,
    has_signal_entry: false,
    // metric_type is undefined
  };

  const sampleResultWithEmptyMetricType: AnalysisResult = {
    ticker: 'AAPL',
    strategy_type: 'EMA',
    short_window: 26,
    long_window: 45,
    signal_window: 0,
    direction: 'Long',
    timeframe: 'D',
    total_trades: 75,
    win_rate: 0.6,
    profit_factor: 2.2,
    expectancy_per_trade: 600.0,
    sortino_ratio: 1.8,
    max_drawdown: 25.0,
    total_return: 200.0,
    annual_return: 30.0,
    sharpe_ratio: 1.5,
    winning_trades: 45,
    losing_trades: 30,
    score: 1.3,
    beats_bnh: 15.0,
    has_open_trade: false,
    has_signal_entry: true,
    metric_type: '',
  };

  describe('basic rendering with metric_type', () => {
    it('should render table with results containing metric_type', () => {
      render(<ResultsTable results={[sampleResultWithMetricType]} />);

      expect(screen.getByText('BTC-USD')).toBeInTheDocument();
      expect(screen.getByText('EMA')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();

      // Expand button should be present
      const expandButton = screen.getByTitle('Expand details');
      expect(expandButton).toBeInTheDocument();
    });

    it('should not show expanded row details initially', () => {
      render(<ResultsTable results={[sampleResultWithMetricType]} />);

      // Metric type details should not be visible initially
      expect(screen.queryByText('Metric Type:')).not.toBeInTheDocument();
      expect(screen.queryByText('Most Sharpe Ratio')).not.toBeInTheDocument();
    });
  });

  describe('expandable row functionality with metric_type', () => {
    it('should expand row and show metric_type as badges when clicked', () => {
      render(<ResultsTable results={[sampleResultWithMetricType]} />);

      const expandButton = screen.getByTitle('Expand details');
      fireEvent.click(expandButton);

      // Should show metric type label
      expect(screen.getByText('Metric Type:')).toBeInTheDocument();

      // Should show individual metric types as badges
      expect(screen.getByText('Most Sharpe Ratio')).toBeInTheDocument();
      expect(screen.getByText('Most Total Return [%]')).toBeInTheDocument();

      // Should have badge styling classes
      const badges = Array.from(document.querySelectorAll('.badge.bg-primary.text-white'));
      expect(badges).toHaveLength(2);
    });

    it('should collapse row when expand button is clicked again', () => {
      render(<ResultsTable results={[sampleResultWithMetricType]} />);

      const expandButton = screen.getByTitle('Expand details');

      // Expand
      fireEvent.click(expandButton);
      expect(screen.getByText('Metric Type:')).toBeInTheDocument();

      // Collapse
      fireEvent.click(expandButton);
      expect(screen.queryByText('Metric Type:')).not.toBeInTheDocument();
      expect(screen.queryByText('Most Sharpe Ratio')).not.toBeInTheDocument();
    });

    it('should update expand button title and icon when expanded', () => {
      render(<ResultsTable results={[sampleResultWithMetricType]} />);

      let expandButton = screen.getByTitle('Expand details');
      expect(document.querySelector('[data-icon="chevron-right"]')).toBeInTheDocument();

      // Click to expand
      fireEvent.click(expandButton);

      expandButton = screen.getByTitle('Collapse details');
      expect(document.querySelector('[data-icon="chevron-down"]')).toBeInTheDocument();
    });
  });

  describe('metric_type display variations', () => {
    it('should handle single metric type correctly', () => {
      const singleMetricResult = {
        ...sampleResultWithMetricType,
        metric_type: 'Most Sharpe Ratio',
      };

      render(<ResultsTable results={[singleMetricResult]} />);

      const expandButton = screen.getByTitle('Expand details');
      fireEvent.click(expandButton);

      expect(screen.getByText('Metric Type:')).toBeInTheDocument();
      expect(screen.getByText('Most Sharpe Ratio')).toBeInTheDocument();

      const badges = Array.from(document.querySelectorAll('.badge.bg-primary.text-white'));
      expect(badges).toHaveLength(1);
    });

    it('should handle multiple comma-separated metric types', () => {
      const multipleMetricResult = {
        ...sampleResultWithMetricType,
        metric_type:
          'Most Omega Ratio, Most Sharpe Ratio, Most Sortino Ratio, Most Total Return [%], Median Total Trades',
      };

      render(<ResultsTable results={[multipleMetricResult]} />);

      const expandButton = screen.getByTitle('Expand details');
      fireEvent.click(expandButton);

      expect(screen.getByText('Metric Type:')).toBeInTheDocument();
      expect(screen.getByText('Most Omega Ratio')).toBeInTheDocument();
      expect(screen.getByText('Most Sharpe Ratio')).toBeInTheDocument();
      expect(screen.getByText('Most Sortino Ratio')).toBeInTheDocument();
      expect(screen.getByText('Most Total Return [%]')).toBeInTheDocument();
      expect(screen.getByText('Median Total Trades')).toBeInTheDocument();

      const badges = Array.from(document.querySelectorAll('.badge.bg-primary.text-white'));
      expect(badges).toHaveLength(5);
    });

    it('should handle metric types with special characters', () => {
      const specialCharsResult = {
        ...sampleResultWithMetricType,
        metric_type: 'Most Total Return [%], Mean Avg Winning Trade [%]',
      };

      render(<ResultsTable results={[specialCharsResult]} />);

      const expandButton = screen.getByTitle('Expand details');
      fireEvent.click(expandButton);

      expect(screen.getByText('Most Total Return [%]')).toBeInTheDocument();
      expect(
        screen.getByText('Mean Avg Winning Trade [%]')
      ).toBeInTheDocument();
    });

    it('should handle empty metric_type gracefully', () => {
      render(<ResultsTable results={[sampleResultWithEmptyMetricType]} />);

      const expandButton = screen.getByTitle('Expand details');
      fireEvent.click(expandButton);

      expect(screen.getByText('Metric Type:')).toBeInTheDocument();
      expect(
        screen.getByText('No metric type data available')
      ).toBeInTheDocument();
      expect(
        document.querySelector('.badge.bg-primary.text-white')
      ).not.toBeInTheDocument();
    });

    it('should handle undefined metric_type gracefully', () => {
      render(<ResultsTable results={[sampleResultWithoutMetricType]} />);

      const expandButton = screen.getByTitle('Expand details');
      fireEvent.click(expandButton);

      expect(screen.getByText('Metric Type:')).toBeInTheDocument();
      expect(
        screen.getByText('No metric type data available')
      ).toBeInTheDocument();
      expect(
        document.querySelector('.badge.bg-primary.text-white')
      ).not.toBeInTheDocument();
    });

    it('should handle metric_type with only whitespace', () => {
      const whitespaceResult = {
        ...sampleResultWithMetricType,
        metric_type: '   ',
      };

      render(<ResultsTable results={[whitespaceResult]} />);

      const expandButton = screen.getByTitle('Expand details');
      fireEvent.click(expandButton);

      expect(screen.getByText('Metric Type:')).toBeInTheDocument();
      expect(
        screen.getByText('No metric type data available')
      ).toBeInTheDocument();
    });

    it('should handle metric_type with empty comma-separated values', () => {
      const emptyCommaResult = {
        ...sampleResultWithMetricType,
        metric_type: 'Most Sharpe Ratio, , ,Most Total Return [%]',
      };

      render(<ResultsTable results={[emptyCommaResult]} />);

      const expandButton = screen.getByTitle('Expand details');
      fireEvent.click(expandButton);

      expect(screen.getByText('Most Sharpe Ratio')).toBeInTheDocument();
      expect(screen.getByText('Most Total Return [%]')).toBeInTheDocument();

      const badges = Array.from(document.querySelectorAll('.badge.bg-primary.text-white'));
      expect(badges).toHaveLength(2); // Should filter out empty values
    });
  });

  describe('multiple rows with different metric_types', () => {
    it('should handle multiple rows with different metric_types independently', () => {
      const results = [
        {
          ...sampleResultWithMetricType,
          ticker: 'BTC-USD',
          metric_type: 'Most Sharpe Ratio',
        },
        {
          ...sampleResultWithoutMetricType,
          ticker: 'ETH-USD',
          // metric_type is undefined
        },
        {
          ...sampleResultWithEmptyMetricType,
          ticker: 'AAPL',
          metric_type: 'Most Total Return [%], Most Sortino Ratio',
        },
      ];

      render(<ResultsTable results={results} />);

      const expandButtons = screen.getAllByTitle('Expand details');
      expect(expandButtons).toHaveLength(3);

      // Expand first row (BTC-USD)
      fireEvent.click(expandButtons[0]);
      expect(screen.getByText('Most Sharpe Ratio')).toBeInTheDocument();

      // Expand second row (ETH-USD)
      fireEvent.click(expandButtons[1]);
      expect(screen.getAllByText('No metric type data available')).toHaveLength(
        1
      );

      // Expand third row (AAPL)
      fireEvent.click(expandButtons[2]);
      expect(screen.getByText('Most Total Return [%]')).toBeInTheDocument();
      expect(screen.getByText('Most Sortino Ratio')).toBeInTheDocument();

      // All should be visible simultaneously
      expect(screen.getByText('Most Sharpe Ratio')).toBeInTheDocument();
      expect(
        screen.getByText('No metric type data available')
      ).toBeInTheDocument();
      expect(screen.getByText('Most Total Return [%]')).toBeInTheDocument();
      expect(screen.getByText('Most Sortino Ratio')).toBeInTheDocument();
    });

    it('should maintain expansion state independently for each row', () => {
      const results = [
        { ...sampleResultWithMetricType, ticker: 'BTC-USD' },
        { ...sampleResultWithoutMetricType, ticker: 'ETH-USD' },
      ];

      render(<ResultsTable results={results} />);

      const expandButtons = screen.getAllByTitle('Expand details');

      // Expand first row
      fireEvent.click(expandButtons[0]);
      expect(screen.getByText('Most Sharpe Ratio')).toBeInTheDocument();

      // Expand second row
      fireEvent.click(expandButtons[1]);
      expect(
        screen.getByText('No metric type data available')
      ).toBeInTheDocument();

      // Collapse first row - second should remain expanded
      fireEvent.click(expandButtons[0]);
      expect(screen.queryByText('Most Sharpe Ratio')).not.toBeInTheDocument();
      expect(
        screen.getByText('No metric type data available')
      ).toBeInTheDocument();
    });
  });

  describe('edge cases and error scenarios', () => {
    it('should handle empty results array', () => {
      render(<ResultsTable results={[]} />);

      expect(
        screen.getByText(
          'No results to display. Run an analysis to see results.'
        )
      ).toBeInTheDocument();
      expect(screen.queryByTitle('Expand details')).not.toBeInTheDocument();
    });

    it('should handle loading state', () => {
      render(<ResultsTable results={[]} isLoading={true} />);

      expect(screen.getByText('Loading results...')).toBeInTheDocument();
      expect(screen.queryByTitle('Expand details')).not.toBeInTheDocument();
    });

    it('should handle error state', () => {
      render(<ResultsTable results={[]} error="Test error message" />);

      expect(screen.getByText('Test error message')).toBeInTheDocument();
      expect(screen.queryByTitle('Expand details')).not.toBeInTheDocument();
    });
  });

  describe('CSS classes and styling', () => {
    it('should apply correct CSS classes to expanded row elements', () => {
      render(<ResultsTable results={[sampleResultWithMetricType]} />);

      const expandButton = screen.getByTitle('Expand details');
      fireEvent.click(expandButton);

      // Check for expanded row classes
      const expandedRow = document.querySelector('.expanded-row');
      expect(expandedRow).toBeInTheDocument();

      const expandedContent = document.querySelector('.expanded-row-content');
      expect(expandedContent).toBeInTheDocument();

      // Check for definition list structure
      const definitionList = document.querySelector('dl.row.mb-0');
      expect(definitionList).toBeInTheDocument();

      const definitionTerm = document.querySelector('dt.col-sm-3');
      expect(definitionTerm).toBeInTheDocument();
      expect(definitionTerm).toHaveTextContent('Metric Type:');

      const definitionDescription = document.querySelector('dd.col-sm-9');
      expect(definitionDescription).toBeInTheDocument();
    });

    it('should apply badge classes to metric type values', () => {
      render(<ResultsTable results={[sampleResultWithMetricType]} />);

      const expandButton = screen.getByTitle('Expand details');
      fireEvent.click(expandButton);

      const badges = document.querySelectorAll('.badge.bg-primary.text-white');
      expect(badges).toHaveLength(2);

      badges.forEach((badge) => {
        expect(badge).toBeInTheDocument();
      });
    });
  });

});

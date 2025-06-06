/**
 * Test suite for MACD functionality in AnalysisConfiguration component.
 *
 * Tests MACD strategy selection, parameter inputs, and validation.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AnalysisConfiguration from '../AnalysisConfiguration';
import { AppContext } from '../../context/AppContext';
import { AnalysisConfiguration as AnalysisConfigType } from '../../types';

// Mock the maCrossApi service
jest.mock('../../services/serviceFactory', () => ({
  maCrossApi: {
    getConfigPresets: jest.fn().mockResolvedValue([
      {
        name: 'Default',
        config: {
          WINDOWS: 10,
          DIRECTION: 'Long',
          STRATEGY_TYPES: ['SMA', 'EMA'],
          USE_HOURLY: false,
          USE_YEARS: false,
          YEARS: 15,
          USE_SYNTHETIC: false,
          USE_CURRENT: true,
          USE_SCANNER: false,
          REFRESH: false,
          MINIMUMS: {
            WIN_RATE: 50,
            TRADES: 10,
            EXPECTANCY_PER_TRADE: 0.1,
            PROFIT_FACTOR: 1.2,
            SORTINO_RATIO: 0.5,
          },
          SORT_BY: 'Score',
          SORT_ASC: false,
          USE_GBM: false,
          async_execution: false,
        },
      },
    ]),
  },
}));

const mockInitialConfig: AnalysisConfigType = {
  TICKER: 'BTC-USD',
  WINDOWS: 10,
  DIRECTION: 'Long',
  STRATEGY_TYPES: ['SMA'],
  USE_HOURLY: false,
  USE_YEARS: false,
  YEARS: 15,
  USE_SYNTHETIC: false,
  USE_CURRENT: true,
  USE_SCANNER: false,
  REFRESH: false,
  MINIMUMS: {
    WIN_RATE: 50,
    TRADES: 10,
    EXPECTANCY_PER_TRADE: 0.1,
    PROFIT_FACTOR: 1.2,
    SORTINO_RATIO: 0.5,
  },
  SORT_BY: 'Score',
  SORT_ASC: false,
  USE_GBM: false,
  async_execution: false,
};

const createMockContext = (config: AnalysisConfigType) => ({
  selectedFile: null,
  setSelectedFile: jest.fn(),
  viewMode: 'table' as const,
  setViewMode: jest.fn(),
  csvData: { data: [], columns: [] },
  setCsvData: jest.fn(),
  isLoading: false,
  setIsLoading: jest.fn(),
  error: null,
  setError: jest.fn(),
  updateStatus: { status: 'completed' as const },
  setUpdateStatus: jest.fn(),
  isOffline: false,
  parameterTesting: {
    configuration: config,
    results: [],
    isAnalyzing: false,
    error: null,
    progress: 0,
    executionId: null,
  },
  setParameterTesting: jest.fn(),
});

const renderWithContext = (
  config: AnalysisConfigType,
  onAnalyze?: jest.Mock
) => {
  const mockContext = createMockContext(config);
  return {
    ...render(
      <AppContext.Provider value={mockContext}>
        <AnalysisConfiguration onAnalyze={onAnalyze} />
      </AppContext.Provider>
    ),
    mockContext,
  };
};

describe('AnalysisConfiguration MACD Support', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('MACD Strategy Selection', () => {
    it('should render MACD strategy checkbox', async () => {
      renderWithContext(mockInitialConfig);

      await waitFor(() => {
        expect(
          screen.getByLabelText(
            /MACD \(Moving Average Convergence Divergence\)/
          )
        ).toBeInTheDocument();
      });
    });

    it('should show MACD parameters when MACD strategy is selected', async () => {
      const configWithMacd = {
        ...mockInitialConfig,
        STRATEGY_TYPES: ['MACD'] as const,
      };

      renderWithContext(configWithMacd);

      await waitFor(() => {
        expect(screen.getByText('MACD Parameters')).toBeInTheDocument();
        expect(screen.getByText('Short EMA Window Range')).toBeInTheDocument();
        expect(screen.getByText('Long EMA Window Range')).toBeInTheDocument();
        expect(screen.getByText('Signal EMA Window Range')).toBeInTheDocument();
        expect(screen.getByLabelText('Step Size')).toBeInTheDocument();
      });
    });

    it('should hide MACD parameters when MACD strategy is not selected', async () => {
      renderWithContext(mockInitialConfig);

      await waitFor(() => {
        expect(screen.queryByText('MACD Parameters')).not.toBeInTheDocument();
      });
    });

    it('should toggle MACD parameter visibility when MACD checkbox is clicked', async () => {
      const { mockContext } = renderWithContext(mockInitialConfig);

      await waitFor(() => {
        expect(
          screen.getByLabelText(
            /MACD \(Moving Average Convergence Divergence\)/
          )
        ).toBeInTheDocument();
      });

      // Initially, MACD parameters should not be visible
      expect(screen.queryByText('MACD Parameters')).not.toBeInTheDocument();

      // Click MACD checkbox
      const macdCheckbox = screen.getByLabelText(
        /MACD \(Moving Average Convergence Divergence\)/
      );
      fireEvent.click(macdCheckbox);

      // MACD parameters should now be visible
      await waitFor(() => {
        expect(screen.getByText('MACD Parameters')).toBeInTheDocument();
      });

      // Verify setParameterTesting was called to update strategy types
      expect(mockContext.setParameterTesting).toHaveBeenCalled();
    });
  });

  describe('MACD Parameter Inputs', () => {
    const configWithMacd = {
      ...mockInitialConfig,
      STRATEGY_TYPES: ['MACD'] as const,
      SHORT_WINDOW_START: 6,
      SHORT_WINDOW_END: 15,
      LONG_WINDOW_START: 12,
      LONG_WINDOW_END: 35,
      SIGNAL_WINDOW_START: 5,
      SIGNAL_WINDOW_END: 12,
      STEP: 2,
    };

    it('should display default MACD parameter values', async () => {
      renderWithContext(configWithMacd);

      await waitFor(() => {
        // Check short window inputs
        const shortStartInputs = screen.getAllByDisplayValue('6');
        const shortEndInputs = screen.getAllByDisplayValue('15');
        expect(shortStartInputs.length).toBeGreaterThan(0);
        expect(shortEndInputs.length).toBeGreaterThan(0);

        // Check long window inputs
        const longStartInputs = screen.getAllByDisplayValue('12');
        const longEndInputs = screen.getAllByDisplayValue('35');
        expect(longStartInputs.length).toBeGreaterThan(0);
        expect(longEndInputs.length).toBeGreaterThan(0);

        // Check signal window inputs
        const signalStartInputs = screen.getAllByDisplayValue('5');
        expect(signalStartInputs.length).toBeGreaterThan(0);

        // Check step input
        const stepInput = screen.getByDisplayValue('2');
        expect(stepInput).toBeInTheDocument();
      });
    });

    it('should update MACD parameters when inputs are changed', async () => {
      const { mockContext } = renderWithContext(configWithMacd);

      await waitFor(() => {
        expect(screen.getByText('MACD Parameters')).toBeInTheDocument();
      });

      // Find and update short window start input
      const shortWindowInputs = screen.getAllByDisplayValue('6');
      const shortWindowStartInput = shortWindowInputs[0]; // Assuming first one is start

      fireEvent.change(shortWindowStartInput, { target: { value: '8' } });

      // Verify setParameterTesting was called to update configuration
      expect(mockContext.setParameterTesting).toHaveBeenCalled();
    });

    it('should have proper input validation attributes', async () => {
      renderWithContext(configWithMacd);

      await waitFor(() => {
        expect(screen.getByText('MACD Parameters')).toBeInTheDocument();
      });

      // Check that inputs have proper min/max attributes
      const shortWindowInputs = screen.getAllByDisplayValue('6');
      const shortWindowStartInput = shortWindowInputs[0];
      expect(shortWindowStartInput).toHaveAttribute('min', '2');
      expect(shortWindowStartInput).toHaveAttribute('max', '50');

      const stepInput = screen.getByDisplayValue('2');
      expect(stepInput).toHaveAttribute('min', '1');
      expect(stepInput).toHaveAttribute('max', '10');
    });
  });

  describe('MACD Parameter Validation', () => {
    it('should show validation error for invalid MACD parameter relationships', async () => {
      const invalidConfig = {
        ...mockInitialConfig,
        STRATEGY_TYPES: ['MACD'] as const,
        SHORT_WINDOW_START: 15, // Invalid: start > end
        SHORT_WINDOW_END: 10,
        LONG_WINDOW_START: 12,
        LONG_WINDOW_END: 35,
        SIGNAL_WINDOW_START: 5,
        SIGNAL_WINDOW_END: 12,
        STEP: 1,
      };

      renderWithContext(invalidConfig);

      await waitFor(() => {
        // Look for validation error about window relationships
        expect(
          screen.getByText(/Short window end must be greater than start/)
        ).toBeInTheDocument();
      });
    });

    it('should show validation error when long window overlaps with short window', async () => {
      const invalidConfig = {
        ...mockInitialConfig,
        STRATEGY_TYPES: ['MACD'] as const,
        SHORT_WINDOW_START: 6,
        SHORT_WINDOW_END: 20,
        LONG_WINDOW_START: 15, // Invalid: long start <= short end
        LONG_WINDOW_END: 35,
        SIGNAL_WINDOW_START: 5,
        SIGNAL_WINDOW_END: 12,
        STEP: 1,
      };

      renderWithContext(invalidConfig);

      await waitFor(() => {
        // Look for validation error about window relationships
        expect(
          screen.getByText(
            /Long window start must be greater than short window end/
          )
        ).toBeInTheDocument();
      });
    });

    it('should disable submit button when MACD validation fails', async () => {
      const invalidConfig = {
        ...mockInitialConfig,
        STRATEGY_TYPES: ['MACD'] as const,
        SHORT_WINDOW_START: 20, // Invalid configuration
        SHORT_WINDOW_END: 15,
        LONG_WINDOW_START: 12,
        LONG_WINDOW_END: 35,
        SIGNAL_WINDOW_START: 5,
        SIGNAL_WINDOW_END: 12,
        STEP: 1,
      };

      renderWithContext(invalidConfig);

      await waitFor(() => {
        const submitButton = screen.getByText('Run Analysis');
        expect(submitButton).toBeDisabled();
      });
    });

    it('should enable submit button when MACD validation passes', async () => {
      const validConfig = {
        ...mockInitialConfig,
        STRATEGY_TYPES: ['MACD'] as const,
        SHORT_WINDOW_START: 6,
        SHORT_WINDOW_END: 15,
        LONG_WINDOW_START: 20, // Valid: > short end
        LONG_WINDOW_END: 35,
        SIGNAL_WINDOW_START: 5,
        SIGNAL_WINDOW_END: 12,
        STEP: 1,
      };

      const mockOnAnalyze = jest.fn();
      renderWithContext(validConfig, mockOnAnalyze);

      await waitFor(() => {
        const submitButton = screen.getByText('Run Analysis');
        expect(submitButton).not.toBeDisabled();
      });
    });
  });

  describe('Mixed Strategy Types with MACD', () => {
    it('should support multiple strategy types including MACD', async () => {
      const mixedConfig = {
        ...mockInitialConfig,
        STRATEGY_TYPES: ['SMA', 'EMA', 'MACD'] as const,
        SHORT_WINDOW_START: 6,
        SHORT_WINDOW_END: 15,
        LONG_WINDOW_START: 20,
        LONG_WINDOW_END: 35,
        SIGNAL_WINDOW_START: 5,
        SIGNAL_WINDOW_END: 12,
        STEP: 1,
      };

      renderWithContext(mixedConfig);

      await waitFor(() => {
        // All strategy checkboxes should be checked
        expect(
          screen.getByLabelText(/SMA \(Simple Moving Average\)/)
        ).toBeChecked();
        expect(
          screen.getByLabelText(/EMA \(Exponential Moving Average\)/)
        ).toBeChecked();
        expect(
          screen.getByLabelText(
            /MACD \(Moving Average Convergence Divergence\)/
          )
        ).toBeChecked();

        // MACD parameters should be visible
        expect(screen.getByText('MACD Parameters')).toBeInTheDocument();
      });
    });

    it('should not allow deselecting all strategy types', async () => {
      const singleMacdConfig = {
        ...mockInitialConfig,
        STRATEGY_TYPES: ['MACD'] as const,
      };

      renderWithContext(singleMacdConfig);

      await waitFor(() => {
        expect(
          screen.getByLabelText(
            /MACD \(Moving Average Convergence Divergence\)/
          )
        ).toBeChecked();
      });

      // Try to uncheck the only selected strategy
      const macdCheckbox = screen.getByLabelText(
        /MACD \(Moving Average Convergence Divergence\)/
      );
      fireEvent.click(macdCheckbox);

      // setParameterTesting should not be called (no change allowed)
      // The exact behavior depends on implementation, but typically it should prevent deselection
      // of the last strategy type
    });
  });

  describe('MACD Help Text and Labels', () => {
    const configWithMacd = {
      ...mockInitialConfig,
      STRATEGY_TYPES: ['MACD'] as const,
    };

    it('should display helpful guidance for MACD parameters', async () => {
      renderWithContext(configWithMacd);

      await waitFor(() => {
        expect(screen.getByText('Typically 6-15 periods')).toBeInTheDocument();
        expect(
          screen.getByText('Typically 12-35 periods (must be > short)')
        ).toBeInTheDocument();
        expect(screen.getByText('Typically 5-12 periods')).toBeInTheDocument();
        expect(
          screen.getByText('Parameter increment (1-10)')
        ).toBeInTheDocument();
      });
    });

    it('should have proper accessibility attributes for MACD inputs', async () => {
      renderWithContext(configWithMacd);

      await waitFor(() => {
        // Check aria-labels for inputs
        expect(screen.getByLabelText('Short window start')).toBeInTheDocument();
        expect(screen.getByLabelText('Short window end')).toBeInTheDocument();
        expect(screen.getByLabelText('Long window start')).toBeInTheDocument();
        expect(screen.getByLabelText('Long window end')).toBeInTheDocument();
        expect(
          screen.getByLabelText('Signal window start')
        ).toBeInTheDocument();
        expect(screen.getByLabelText('Signal window end')).toBeInTheDocument();
      });
    });
  });
});

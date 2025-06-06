import React, { useState, useCallback, useEffect } from 'react';
import Icon from './Icon';
import { icons } from '../utils/icons';
import { useAppContext } from '../context/AppContext';
import { AnalysisConfiguration as AnalysisConfigType } from '../types';
import { maCrossApi } from '../services/serviceFactory';
import { ConfigPreset } from '../services/maCrossApi';
import { TickerPresets } from './TickerPresets';

interface FormErrors {
  TICKER?: string;
  WINDOWS?: string;
  YEARS?: string;
}

interface AnalysisConfigurationProps {
  onAnalyze?: (config: AnalysisConfigType) => Promise<void>;
  isAnalyzing?: boolean;
}

const AnalysisConfiguration: React.FC<AnalysisConfigurationProps> = React.memo(
  ({ onAnalyze, isAnalyzing = false }) => {
    const { parameterTesting, setParameterTesting } = useAppContext();
    const [formErrors, setFormErrors] = useState<FormErrors>({});
    const [selectedPreset, setSelectedPreset] = useState<string>('');
    const [presets, setPresets] = useState<ConfigPreset[]>([]);
    const [loadingPresets, setLoadingPresets] = useState(true);
    const [presetsError, setPresetsError] = useState<string | null>(null);
    const [isAdvancedExpanded, setIsAdvancedExpanded] = useState(false);

    // Load presets from API on component mount
    useEffect(() => {
      const loadPresets = async () => {
        try {
          setLoadingPresets(true);
          setPresetsError(null);
          const loadedPresets = await maCrossApi.getConfigPresets();
          setPresets(loadedPresets);
        } catch (error) {
          console.error('Failed to load configuration presets:', error);
          setPresetsError(
            error instanceof Error ? error.message : 'Failed to load presets'
          );
        } finally {
          setLoadingPresets(false);
        }
      };

      loadPresets();
    }, []);

    // Handle Bootstrap collapse events for advanced configuration
    useEffect(() => {
      const advancedElement = document.getElementById('advanced-configuration');
      if (!advancedElement) return;

      const handleShow = () => setIsAdvancedExpanded(true);
      const handleHide = () => setIsAdvancedExpanded(false);

      advancedElement.addEventListener('show.bs.collapse', handleShow);
      advancedElement.addEventListener('hide.bs.collapse', handleHide);

      return () => {
        advancedElement.removeEventListener('show.bs.collapse', handleShow);
        advancedElement.removeEventListener('hide.bs.collapse', handleHide);
      };
    }, []);

    const updateConfiguration = useCallback(
      (updates: Partial<AnalysisConfigType>) => {
        setParameterTesting({
          ...parameterTesting,
          configuration: {
            ...parameterTesting.configuration,
            ...updates,
          },
        });
      },
      [parameterTesting, setParameterTesting]
    );

    // Auto-select Default preset when presets are loaded
    useEffect(() => {
      if (presets.length > 0 && !selectedPreset && !loadingPresets) {
        const defaultPreset = presets.find((p) => p.name === 'Default');
        if (defaultPreset) {
          // Apply the default preset configuration
          const currentTicker = parameterTesting.configuration.TICKER;

          // Convert API config format to frontend format
          const convertedConfig = {
            ...defaultPreset.config,
            TICKER: currentTicker, // Keep current ticker
            SORT_BY:
              defaultPreset.config.SORT_BY === 'Score'
                ? 'Score'
                : 'Expectancy per Trade',
            MINIMUMS: {
              ...parameterTesting.configuration.MINIMUMS,
              // WIN_RATE is already in percentage format from the preset
              WIN_RATE:
                defaultPreset.config.MINIMUMS?.WIN_RATE !== undefined
                  ? defaultPreset.config.MINIMUMS.WIN_RATE
                  : parameterTesting.configuration.MINIMUMS.WIN_RATE,
              TRADES:
                defaultPreset.config.MINIMUMS?.TRADES ||
                parameterTesting.configuration.MINIMUMS.TRADES,
              EXPECTANCY_PER_TRADE:
                defaultPreset.config.MINIMUMS?.EXPECTANCY_PER_TRADE ||
                parameterTesting.configuration.MINIMUMS.EXPECTANCY_PER_TRADE,
              PROFIT_FACTOR:
                defaultPreset.config.MINIMUMS?.PROFIT_FACTOR ||
                parameterTesting.configuration.MINIMUMS.PROFIT_FACTOR,
              SORTINO_RATIO:
                defaultPreset.config.MINIMUMS?.SORTINO_RATIO ||
                parameterTesting.configuration.MINIMUMS.SORTINO_RATIO,
            },
          };

          updateConfiguration(convertedConfig);
          setSelectedPreset('Default');
        }
      }
    }, [
      presets,
      selectedPreset,
      loadingPresets,
      parameterTesting.configuration,
      updateConfiguration,
    ]);

    const validateTicker = (value: string): string | undefined => {
      if (!value.trim()) {
        return 'Ticker symbol is required';
      }
      // Basic validation for ticker symbols (alphanumeric, commas, spaces, hyphens)
      const tickerRegex = /^[A-Za-z0-9,\s\-=.]+$/;
      if (!tickerRegex.test(value)) {
        return 'Invalid ticker format. Use alphanumeric characters, commas, spaces, and hyphens only.';
      }
      return undefined;
    };

    const validateWindows = (value: number): string | undefined => {
      if (value < 1 || value > 50) {
        return 'Windows must be between 1 and 50';
      }
      return undefined;
    };

    const validateYears = (value: number): string | undefined => {
      if (value < 1 || value > 50) {
        return 'Years must be between 1 and 50';
      }
      return undefined;
    };

    const validateMACDParameters = (): string | undefined => {
      if (!parameterTesting.configuration.STRATEGY_TYPES.includes('MACD')) {
        return undefined;
      }

      const shortStart = parameterTesting.configuration.SHORT_WINDOW_START || 6;
      const shortEnd = parameterTesting.configuration.SHORT_WINDOW_END || 15;
      const longStart = parameterTesting.configuration.LONG_WINDOW_START || 12;
      const longEnd = parameterTesting.configuration.LONG_WINDOW_END || 35;
      const signalStart =
        parameterTesting.configuration.SIGNAL_WINDOW_START || 5;
      const signalEnd = parameterTesting.configuration.SIGNAL_WINDOW_END || 12;

      if (shortStart >= shortEnd) {
        return 'Short window end must be greater than start';
      }
      if (longStart >= longEnd) {
        return 'Long window end must be greater than start';
      }
      if (signalStart >= signalEnd) {
        return 'Signal window end must be greater than start';
      }
      if (longStart <= shortEnd) {
        return 'Long window start must be greater than short window end';
      }

      return undefined;
    };

    const handleTickerChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      const error = validateTicker(value);

      setFormErrors((prev) => ({ ...prev, TICKER: error }));
      updateConfiguration({ TICKER: value });
    };

    const handleWindowsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = parseInt(e.target.value);
      const error = validateWindows(value);

      setFormErrors((prev) => ({ ...prev, WINDOWS: error }));
      updateConfiguration({ WINDOWS: value });
    };

    const handleDirectionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      updateConfiguration({ DIRECTION: e.target.value as 'Long' | 'Short' });
    };

    const handleStrategyTypeChange = (
      strategyType: 'SMA' | 'EMA' | 'MACD',
      checked: boolean
    ) => {
      const currentTypes = parameterTesting.configuration.STRATEGY_TYPES;
      let newTypes: ('SMA' | 'EMA' | 'MACD')[];

      if (checked) {
        newTypes = [...currentTypes, strategyType];
      } else {
        newTypes = currentTypes.filter((type) => type !== strategyType);
      }

      // Ensure at least one strategy type is selected
      if (newTypes.length === 0) {
        return; // Don't allow deselecting all strategy types
      }

      updateConfiguration({ STRATEGY_TYPES: newTypes });
    };

    const handleOptionChange = (
      option: keyof AnalysisConfigType,
      checked: boolean
    ) => {
      updateConfiguration({ [option]: checked });
    };

    const handleYearsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = parseInt(e.target.value);
      const error = validateYears(value);

      setFormErrors((prev) => ({ ...prev, YEARS: error }));
      updateConfiguration({ YEARS: value });
    };

    const handleMinimumChange = (
      field: keyof AnalysisConfigType['MINIMUMS'],
      value: number
    ) => {
      updateConfiguration({
        MINIMUMS: {
          ...parameterTesting.configuration.MINIMUMS,
          [field]: value,
        },
      });
    };

    const handleSortByChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      updateConfiguration({ SORT_BY: e.target.value });
    };

    const loadPreset = (presetName: string) => {
      const preset = presets.find((p) => p.name === presetName);
      if (preset) {
        // Preserve the current TICKER value when loading a preset
        const currentTicker = parameterTesting.configuration.TICKER;

        // Convert API config format to frontend format
        const convertedConfig = {
          ...preset.config,
          TICKER: currentTicker, // Keep current ticker
          SORT_BY:
            preset.config.SORT_BY === 'Score'
              ? 'Score'
              : 'Expectancy per Trade',
          MINIMUMS: {
            ...parameterTesting.configuration.MINIMUMS,
            // WIN_RATE is already in percentage format from the preset
            WIN_RATE:
              preset.config.MINIMUMS?.WIN_RATE !== undefined
                ? preset.config.MINIMUMS.WIN_RATE
                : parameterTesting.configuration.MINIMUMS.WIN_RATE,
            TRADES:
              preset.config.MINIMUMS?.TRADES ||
              parameterTesting.configuration.MINIMUMS.TRADES,
            EXPECTANCY_PER_TRADE:
              preset.config.MINIMUMS?.EXPECTANCY_PER_TRADE ||
              parameterTesting.configuration.MINIMUMS.EXPECTANCY_PER_TRADE,
            PROFIT_FACTOR:
              preset.config.MINIMUMS?.PROFIT_FACTOR ||
              parameterTesting.configuration.MINIMUMS.PROFIT_FACTOR,
            SORTINO_RATIO:
              preset.config.MINIMUMS?.SORTINO_RATIO ||
              parameterTesting.configuration.MINIMUMS.SORTINO_RATIO,
          },
        };

        updateConfiguration(convertedConfig);
        setSelectedPreset(presetName);
        // Clear any validation errors when loading a preset
        setFormErrors({});
      }
    };

    const handlePresetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      const presetName = e.target.value;
      if (presetName === '') {
        setSelectedPreset('');
        return;
      }
      loadPreset(presetName);
    };

    const isFormValid = (): boolean => {
      const hasErrors = Object.values(formErrors).some(
        (error) => error !== undefined
      );
      const ticker = parameterTesting.configuration.TICKER;
      const tickerValue = Array.isArray(ticker) ? ticker.join(', ') : ticker;
      const hasRequiredFields = tickerValue.trim() !== '';
      const macdError = validateMACDParameters();
      return !hasErrors && hasRequiredFields && !macdError;
    };

    return (
      <div className="card mb-4">
        <div className="card-header d-flex align-items-center">
          <Icon icon={icons.settings} className="me-2" />
          <h6 className="card-title mb-0">Analysis Configuration</h6>
        </div>
        <div className="card-body">
          <div className="row g-3">
            {/* Configuration Presets */}
            <div className="col-md-4">
              <label htmlFor="preset-select" className="form-label">
                <Icon icon={icons.settings} className="me-1" />
                Configuration Preset
              </label>
              <select
                className="form-select"
                id="preset-select"
                value={selectedPreset}
                onChange={handlePresetChange}
                aria-describedby="preset-help"
                disabled={loadingPresets}
              >
                <option value="">
                  {loadingPresets ? 'Loading presets...' : 'Choose a preset...'}
                </option>
                {presets.map((preset) => (
                  <option key={preset.name} value={preset.name}>
                    {preset.name}
                  </option>
                ))}
              </select>
              <div id="preset-help" className="form-text">
                {presetsError ? (
                  <span className="text-danger">Error: {presetsError}</span>
                ) : (
                  'Quick configuration templates'
                )}
              </div>
            </div>

            {/* Ticker Presets */}
            <div className="col-md-4">
              <TickerPresets
                onTickersChange={(tickers) => {
                  updateConfiguration({ TICKER: tickers });
                  // Clear any validation errors when tickers are loaded from preset
                  setFormErrors((prev) => ({ ...prev, TICKER: undefined }));
                }}
                currentTickers={
                  Array.isArray(parameterTesting.configuration.TICKER)
                    ? parameterTesting.configuration.TICKER.join(',')
                    : parameterTesting.configuration.TICKER
                }
              />
            </div>

            {/* Ticker Input - Full Width */}
            <div className="col-12">
              <label htmlFor="ticker-input" className="form-label">
                <Icon icon={icons.search} className="me-1" />
                Ticker Symbol(s) <span className="text-danger">*</span>
              </label>
              <input
                type="text"
                className={`form-control ${
                  formErrors.TICKER ? 'is-invalid' : ''
                }`}
                id="ticker-input"
                placeholder="e.g., AAPL, GOOGL, MSFT"
                value={
                  Array.isArray(parameterTesting.configuration.TICKER)
                    ? parameterTesting.configuration.TICKER.join(', ')
                    : parameterTesting.configuration.TICKER
                }
                onChange={handleTickerChange}
                aria-describedby="ticker-help"
                aria-required="true"
                aria-invalid={!!formErrors.TICKER}
              />
              {formErrors.TICKER && (
                <div className="invalid-feedback" role="alert">
                  {formErrors.TICKER}
                </div>
              )}
              <div id="ticker-help" className="form-text">
                Comma-separated list of ticker symbols
              </div>
            </div>

            <div className="col-md-3">
              <label htmlFor="windows-input" className="form-label">
                <Icon icon={icons.calculator} className="me-1" />
                Windows
              </label>
              <input
                type="number"
                className={`form-control ${
                  formErrors.WINDOWS ? 'is-invalid' : ''
                }`}
                id="windows-input"
                value={parameterTesting.configuration.WINDOWS}
                min="1"
                max="50"
                onChange={handleWindowsChange}
                aria-describedby="windows-help"
                aria-invalid={!!formErrors.WINDOWS}
              />
              {formErrors.WINDOWS && (
                <div className="invalid-feedback" role="alert">
                  {formErrors.WINDOWS}
                </div>
              )}
              <div id="windows-help" className="form-text">
                Number of window combinations (1-50)
              </div>
            </div>

            <div className="col-md-3">
              <label htmlFor="direction-select" className="form-label">
                <Icon icon={icons.chevronUp} className="me-1" />
                Direction
              </label>
              <select
                className="form-select"
                id="direction-select"
                value={parameterTesting.configuration.DIRECTION}
                onChange={handleDirectionChange}
              >
                <option value="Long">Long</option>
                <option value="Short">Short</option>
              </select>
            </div>

            {/* Strategy Types */}
            <div className="col-md-6">
              <label className="form-label">
                <Icon icon={icons.brand} className="me-1" />
                Strategy Types
              </label>
              <div className="d-flex gap-3 flex-wrap">
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    id="sma-checkbox"
                    checked={parameterTesting.configuration.STRATEGY_TYPES.includes(
                      'SMA'
                    )}
                    onChange={(e) =>
                      handleStrategyTypeChange('SMA', e.target.checked)
                    }
                  />
                  <label className="form-check-label" htmlFor="sma-checkbox">
                    SMA (Simple Moving Average)
                  </label>
                </div>
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    id="ema-checkbox"
                    checked={parameterTesting.configuration.STRATEGY_TYPES.includes(
                      'EMA'
                    )}
                    onChange={(e) =>
                      handleStrategyTypeChange('EMA', e.target.checked)
                    }
                  />
                  <label className="form-check-label" htmlFor="ema-checkbox">
                    EMA (Exponential Moving Average)
                  </label>
                </div>
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    id="macd-checkbox"
                    checked={parameterTesting.configuration.STRATEGY_TYPES.includes(
                      'MACD'
                    )}
                    onChange={(e) =>
                      handleStrategyTypeChange('MACD', e.target.checked)
                    }
                  />
                  <label className="form-check-label" htmlFor="macd-checkbox">
                    MACD (Moving Average Convergence Divergence)
                  </label>
                </div>
              </div>
            </div>

            {/* MACD Parameters - Only show when MACD is selected */}
            {parameterTesting.configuration.STRATEGY_TYPES.includes('MACD') && (
              <div className="col-12">
                <div className="card border-primary">
                  <div className="card-header bg-primary bg-opacity-10">
                    <h6 className="card-title mb-0">
                      <Icon icon={icons.calculator} className="me-1" />
                      MACD Parameters
                    </h6>
                  </div>
                  <div className="card-body">
                    <div className="row g-3">
                      <div className="col-md-4">
                        <label className="form-label">
                          Short EMA Window Range
                        </label>
                        <div className="d-flex gap-2">
                          <div>
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              placeholder="Start"
                              value={
                                parameterTesting.configuration
                                  .SHORT_WINDOW_START || 6
                              }
                              min="2"
                              max="50"
                              onChange={(e) =>
                                updateConfiguration({
                                  SHORT_WINDOW_START: parseInt(e.target.value),
                                })
                              }
                              aria-label="Short window start"
                            />
                          </div>
                          <span className="align-self-center">-</span>
                          <div>
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              placeholder="End"
                              value={
                                parameterTesting.configuration
                                  .SHORT_WINDOW_END || 15
                              }
                              min="2"
                              max="50"
                              onChange={(e) =>
                                updateConfiguration({
                                  SHORT_WINDOW_END: parseInt(e.target.value),
                                })
                              }
                              aria-label="Short window end"
                            />
                          </div>
                        </div>
                        <div className="form-text">Typically 6-15 periods</div>
                      </div>

                      <div className="col-md-4">
                        <label className="form-label">
                          Long EMA Window Range
                        </label>
                        <div className="d-flex gap-2">
                          <div>
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              placeholder="Start"
                              value={
                                parameterTesting.configuration
                                  .LONG_WINDOW_START || 12
                              }
                              min="4"
                              max="100"
                              onChange={(e) =>
                                updateConfiguration({
                                  LONG_WINDOW_START: parseInt(e.target.value),
                                })
                              }
                              aria-label="Long window start"
                            />
                          </div>
                          <span className="align-self-center">-</span>
                          <div>
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              placeholder="End"
                              value={
                                parameterTesting.configuration
                                  .LONG_WINDOW_END || 35
                              }
                              min="4"
                              max="100"
                              onChange={(e) =>
                                updateConfiguration({
                                  LONG_WINDOW_END: parseInt(e.target.value),
                                })
                              }
                              aria-label="Long window end"
                            />
                          </div>
                        </div>
                        <div className="form-text">
                          Typically 12-35 periods (must be &gt; short)
                        </div>
                      </div>

                      <div className="col-md-4">
                        <label className="form-label">
                          Signal EMA Window Range
                        </label>
                        <div className="d-flex gap-2">
                          <div>
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              placeholder="Start"
                              value={
                                parameterTesting.configuration
                                  .SIGNAL_WINDOW_START || 5
                              }
                              min="2"
                              max="50"
                              onChange={(e) =>
                                updateConfiguration({
                                  SIGNAL_WINDOW_START: parseInt(e.target.value),
                                })
                              }
                              aria-label="Signal window start"
                            />
                          </div>
                          <span className="align-self-center">-</span>
                          <div>
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              placeholder="End"
                              value={
                                parameterTesting.configuration
                                  .SIGNAL_WINDOW_END || 12
                              }
                              min="2"
                              max="50"
                              onChange={(e) =>
                                updateConfiguration({
                                  SIGNAL_WINDOW_END: parseInt(e.target.value),
                                })
                              }
                              aria-label="Signal window end"
                            />
                          </div>
                        </div>
                        <div className="form-text">Typically 5-12 periods</div>
                      </div>

                      <div className="col-md-4">
                        <label htmlFor="macd-step" className="form-label">
                          Step Size
                        </label>
                        <input
                          type="number"
                          className="form-control form-control-sm"
                          id="macd-step"
                          value={parameterTesting.configuration.STEP || 1}
                          min="1"
                          max="10"
                          onChange={(e) =>
                            updateConfiguration({
                              STEP: parseInt(e.target.value),
                            })
                          }
                        />
                        <div className="form-text">
                          Parameter increment (1-10)
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Basic Options */}
            <div className="col-md-6">
              <label className="form-label">
                <Icon icon={icons.settings} className="me-1" />
                Options
              </label>
              <div className="row g-2">
                <div className="col-6">
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="use-current-checkbox"
                      checked={parameterTesting.configuration.USE_CURRENT}
                      onChange={(e) =>
                        handleOptionChange('USE_CURRENT', e.target.checked)
                      }
                    />
                    <label
                      className="form-check-label"
                      htmlFor="use-current-checkbox"
                    >
                      Use Current Price
                    </label>
                  </div>
                </div>
                <div className="col-6">
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="refresh-checkbox"
                      checked={parameterTesting.configuration.REFRESH}
                      onChange={(e) =>
                        handleOptionChange('REFRESH', e.target.checked)
                      }
                    />
                    <label
                      className="form-check-label"
                      htmlFor="refresh-checkbox"
                    >
                      Refresh Data
                    </label>
                  </div>
                </div>
                <div className="col-6">
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="use-hourly-checkbox"
                      checked={parameterTesting.configuration.USE_HOURLY}
                      onChange={(e) =>
                        handleOptionChange('USE_HOURLY', e.target.checked)
                      }
                    />
                    <label
                      className="form-check-label"
                      htmlFor="use-hourly-checkbox"
                    >
                      Use Hourly Data
                    </label>
                  </div>
                </div>
                <div className="col-6">
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="use-scanner-checkbox"
                      checked={parameterTesting.configuration.USE_SCANNER}
                      onChange={(e) =>
                        handleOptionChange('USE_SCANNER', e.target.checked)
                      }
                    />
                    <label
                      className="form-check-label"
                      htmlFor="use-scanner-checkbox"
                    >
                      Use Scanner
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Advanced Configuration Toggle */}
            <div className="col-12">
              <button
                type="button"
                className="btn btn-outline-secondary btn-sm"
                data-bs-toggle="collapse"
                data-bs-target="#advanced-configuration"
                aria-expanded={isAdvancedExpanded}
                aria-controls="advanced-configuration"
              >
                <Icon
                  icon={
                    isAdvancedExpanded ? icons.chevronUp : icons.chevronDown
                  }
                  className="me-1"
                />
                Advanced Configuration
              </button>
            </div>

            {/* Advanced Configuration (Bootstrap Collapsible) */}
            <div className="col-12">
              <div className="collapse" id="advanced-configuration">
                <div className="card border-secondary">
                  <div className="card-header">
                    <h6 className="card-title mb-0">Advanced Settings</h6>
                  </div>
                  <div className="card-body">
                    <div className="row g-3">
                      {/* Years Configuration */}
                      <div className="col-md-6">
                        <div className="form-check mb-2">
                          <input
                            className="form-check-input"
                            type="checkbox"
                            id="use-years-checkbox"
                            checked={parameterTesting.configuration.USE_YEARS}
                            onChange={(e) =>
                              handleOptionChange('USE_YEARS', e.target.checked)
                            }
                          />
                          <label
                            className="form-check-label"
                            htmlFor="use-years-checkbox"
                          >
                            Use Years Limit
                          </label>
                        </div>
                        {parameterTesting.configuration.USE_YEARS && (
                          <input
                            type="number"
                            className={`form-control ${
                              formErrors.YEARS ? 'is-invalid' : ''
                            }`}
                            placeholder="Years"
                            value={parameterTesting.configuration.YEARS}
                            min="1"
                            max="50"
                            onChange={handleYearsChange}
                          />
                        )}
                        {formErrors.YEARS && (
                          <div className="invalid-feedback">
                            {formErrors.YEARS}
                          </div>
                        )}
                      </div>

                      {/* Additional Options */}
                      <div className="col-md-6">
                        <div className="form-check mb-2">
                          <input
                            className="form-check-input"
                            type="checkbox"
                            id="use-synthetic-checkbox"
                            checked={
                              parameterTesting.configuration.USE_SYNTHETIC
                            }
                            onChange={(e) =>
                              handleOptionChange(
                                'USE_SYNTHETIC',
                                e.target.checked
                              )
                            }
                          />
                          <label
                            className="form-check-label"
                            htmlFor="use-synthetic-checkbox"
                          >
                            Use Synthetic Data
                          </label>
                        </div>
                        <div className="form-check">
                          <input
                            className="form-check-input"
                            type="checkbox"
                            id="use-gbm-checkbox"
                            checked={parameterTesting.configuration.USE_GBM}
                            onChange={(e) =>
                              handleOptionChange('USE_GBM', e.target.checked)
                            }
                          />
                          <label
                            className="form-check-label"
                            htmlFor="use-gbm-checkbox"
                          >
                            Use GBM (Geometric Brownian Motion)
                          </label>
                        </div>
                      </div>

                      {/* Minimums Configuration */}
                      <div className="col-12">
                        <label className="form-label fw-bold">
                          Minimum Thresholds
                        </label>
                        <div className="row g-2">
                          <div className="col-md-2">
                            <label
                              htmlFor="min-win-rate"
                              className="form-label small"
                            >
                              Win Rate %
                            </label>
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              id="min-win-rate"
                              value={
                                parameterTesting.configuration.MINIMUMS.WIN_RATE
                              }
                              min="0"
                              max="100"
                              onChange={(e) =>
                                handleMinimumChange(
                                  'WIN_RATE',
                                  parseFloat(e.target.value)
                                )
                              }
                            />
                          </div>
                          <div className="col-md-2">
                            <label
                              htmlFor="min-trades"
                              className="form-label small"
                            >
                              Trades
                            </label>
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              id="min-trades"
                              value={
                                parameterTesting.configuration.MINIMUMS.TRADES
                              }
                              min="0"
                              onChange={(e) =>
                                handleMinimumChange(
                                  'TRADES',
                                  parseInt(e.target.value)
                                )
                              }
                            />
                          </div>
                          <div className="col-md-3">
                            <label
                              htmlFor="min-expectancy"
                              className="form-label small"
                            >
                              Expectancy per Trade
                            </label>
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              id="min-expectancy"
                              value={
                                parameterTesting.configuration.MINIMUMS
                                  .EXPECTANCY_PER_TRADE
                              }
                              step="0.01"
                              onChange={(e) =>
                                handleMinimumChange(
                                  'EXPECTANCY_PER_TRADE',
                                  parseFloat(e.target.value)
                                )
                              }
                            />
                          </div>
                          <div className="col-md-2">
                            <label
                              htmlFor="min-profit-factor"
                              className="form-label small"
                            >
                              Profit Factor
                            </label>
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              id="min-profit-factor"
                              value={
                                parameterTesting.configuration.MINIMUMS
                                  .PROFIT_FACTOR
                              }
                              step="0.1"
                              min="0"
                              onChange={(e) =>
                                handleMinimumChange(
                                  'PROFIT_FACTOR',
                                  parseFloat(e.target.value)
                                )
                              }
                            />
                          </div>
                          <div className="col-md-3">
                            <label
                              htmlFor="min-sortino-ratio"
                              className="form-label small"
                            >
                              Sortino Ratio
                            </label>
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              id="min-sortino-ratio"
                              value={
                                parameterTesting.configuration.MINIMUMS
                                  .SORTINO_RATIO
                              }
                              step="0.1"
                              onChange={(e) =>
                                handleMinimumChange(
                                  'SORTINO_RATIO',
                                  parseFloat(e.target.value)
                                )
                              }
                            />
                          </div>
                        </div>
                      </div>

                      {/* Sorting Configuration */}
                      <div className="col-md-6">
                        <label htmlFor="sort-by-select" className="form-label">
                          Sort By
                        </label>
                        <select
                          className="form-select"
                          id="sort-by-select"
                          value={parameterTesting.configuration.SORT_BY}
                          onChange={handleSortByChange}
                        >
                          <option value="Expectancy per Trade">
                            Expectancy per Trade
                          </option>
                          <option value="Win Rate [%]">Win Rate</option>
                          <option value="Profit Factor">Profit Factor</option>
                          <option value="Sortino Ratio">Sortino Ratio</option>
                          <option value="Total Trades">Total Trades</option>
                          <option value="Score">Score</option>
                          <option value="Total Return [%]">Total Return</option>
                        </select>
                      </div>

                      <div className="col-md-6">
                        <label className="form-label">Sort Order</label>
                        <div className="d-flex gap-3">
                          <div className="form-check">
                            <input
                              className="form-check-input"
                              type="radio"
                              name="sort-order"
                              id="sort-desc"
                              checked={!parameterTesting.configuration.SORT_ASC}
                              onChange={() =>
                                updateConfiguration({ SORT_ASC: false })
                              }
                            />
                            <label
                              className="form-check-label"
                              htmlFor="sort-desc"
                            >
                              Descending (High to Low)
                            </label>
                          </div>
                          <div className="form-check">
                            <input
                              className="form-check-input"
                              type="radio"
                              name="sort-order"
                              id="sort-asc"
                              checked={parameterTesting.configuration.SORT_ASC}
                              onChange={() =>
                                updateConfiguration({ SORT_ASC: true })
                              }
                            />
                            <label
                              className="form-check-label"
                              htmlFor="sort-asc"
                            >
                              Ascending (Low to High)
                            </label>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Run Analysis Button */}
            <div className="col-12">
              <button
                type="button"
                className="btn btn-primary"
                disabled={isAnalyzing || !isFormValid()}
                onClick={async () => {
                  if (onAnalyze && isFormValid()) {
                    await onAnalyze(parameterTesting.configuration);
                  }
                }}
                aria-describedby={
                  !isFormValid() ? 'validation-error' : undefined
                }
              >
                {isAnalyzing ? (
                  <>
                    <Icon
                      icon={icons.loading}
                      className="me-2 fa-spin"
                      aria-hidden="true"
                    />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Icon
                      icon={icons.parameterTesting}
                      className="me-2"
                      aria-hidden="true"
                    />
                    Run Analysis
                  </>
                )}
              </button>
              {!isFormValid() && (
                <div
                  id="validation-error"
                  className="form-text text-danger"
                  role="alert"
                >
                  {validateMACDParameters() ||
                    'Please fix validation errors and ensure all required fields are filled.'}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }
);

export default AnalysisConfiguration;

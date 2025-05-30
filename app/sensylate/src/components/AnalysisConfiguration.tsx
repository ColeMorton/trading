import React, { useState, useCallback } from 'react';
import Icon from './Icon';
import { icons } from '../utils/icons';
import { useAppContext } from '../context/AppContext';
import { AnalysisConfiguration as AnalysisConfigType } from '../types';

interface FormErrors {
  TICKER?: string;
  WINDOWS?: string;
  YEARS?: string;
}

interface ConfigurationPreset {
  name: string;
  config: Partial<AnalysisConfigType>;
}

interface AnalysisConfigurationProps {
  onAnalyze?: (config: AnalysisConfigType) => Promise<void>;
  isAnalyzing?: boolean;
}

const DEFAULT_PRESETS: ConfigurationPreset[] = [
  {
    name: 'Default',
    config: {
      WINDOWS: 20,
      STRATEGY_TYPES: ['SMA'],
      DIRECTION: 'Long',
      USE_HOURLY: false,
      USE_YEARS: false,
      YEARS: 2,
      USE_SYNTHETIC: false,
      USE_CURRENT: true,
      USE_SCANNER: false,
      REFRESH: false,
      USE_GBM: false,
      SORT_BY: 'Expectancy per Trade',
      SORT_ASC: false,
      MINIMUMS: {
        WIN_RATE: 0,
        TRADES: 1,
        EXPECTANCY_PER_TRADE: 0,
        PROFIT_FACTOR: 0,
        SORTINO_RATIO: 0,
      },
    }
  },
  {
    name: 'Quick Test',
    config: {
      WINDOWS: 8,
      STRATEGY_TYPES: ['SMA', 'EMA'],
      DIRECTION: 'Long',
      USE_HOURLY: false,
      USE_YEARS: true,
      YEARS: 2,
      USE_SYNTHETIC: false,
      USE_CURRENT: false,
      USE_SCANNER: false,
      REFRESH: true,
      USE_GBM: false,
      SORT_BY: 'Expectancy per Trade',
      SORT_ASC: false,
    }
  },
  {
    name: 'Comprehensive Analysis',
    config: {
      WINDOWS: 89,
      STRATEGY_TYPES: ['SMA', 'EMA'],
      DIRECTION: 'Long',
      USE_HOURLY: false,
      USE_YEARS: false,
      YEARS: 15,
      USE_SYNTHETIC: false,
      USE_CURRENT: false,
      USE_SCANNER: false,
      REFRESH: true,
      USE_GBM: false,
      SORT_BY: 'Expectancy per Trade',
      SORT_ASC: false,
    }
  },
  {
    name: 'Hourly Strategy',
    config: {
      WINDOWS: 20,
      STRATEGY_TYPES: ['EMA'],
      DIRECTION: 'Long',
      USE_HOURLY: true,
      USE_YEARS: true,
      YEARS: 1,
      USE_SYNTHETIC: false,
      USE_CURRENT: true,
      USE_SCANNER: false,
      REFRESH: false,
      USE_GBM: false,
      SORT_BY: 'profit_factor',
      SORT_ASC: false,
    }
  },
  {
    name: 'Strict Filter',
    config: {
      WINDOWS: 89,
      STRATEGY_TYPES: ['SMA', 'EMA'],
      DIRECTION: 'Long',
      USE_HOURLY: false,
      USE_YEARS: false,
      YEARS: 15,
      USE_SYNTHETIC: false,
      USE_CURRENT: false,
      USE_SCANNER: false,
      REFRESH: true,
      USE_GBM: false,
      SORT_BY: 'Score',
      SORT_ASC: false,
      MINIMUMS: {
        WIN_RATE: 44,
        TRADES: 54,
        EXPECTANCY_PER_TRADE: 1,
        PROFIT_FACTOR: 1,
        SORTINO_RATIO: 0.4,
      },
    }
  }
];

const AnalysisConfiguration: React.FC<AnalysisConfigurationProps> = React.memo(({ 
  onAnalyze,
  isAnalyzing = false 
}) => {
  const { parameterTesting, setParameterTesting } = useAppContext();
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string>('');

  const updateConfiguration = useCallback((updates: Partial<AnalysisConfigType>) => {
    setParameterTesting({
      ...parameterTesting,
      configuration: {
        ...parameterTesting.configuration,
        ...updates,
      },
    });
  }, [parameterTesting, setParameterTesting]);

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

  const handleTickerChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const error = validateTicker(value);
    
    setFormErrors(prev => ({ ...prev, TICKER: error }));
    updateConfiguration({ TICKER: value });
  };

  const handleWindowsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value);
    const error = validateWindows(value);
    
    setFormErrors(prev => ({ ...prev, WINDOWS: error }));
    updateConfiguration({ WINDOWS: value });
  };

  const handleDirectionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    updateConfiguration({ DIRECTION: e.target.value as 'Long' | 'Short' });
  };

  const handleStrategyTypeChange = (strategyType: 'SMA' | 'EMA', checked: boolean) => {
    const currentTypes = parameterTesting.configuration.STRATEGY_TYPES;
    let newTypes: ('SMA' | 'EMA')[];
    
    if (checked) {
      newTypes = [...currentTypes, strategyType];
    } else {
      newTypes = currentTypes.filter(type => type !== strategyType);
    }
    
    // Ensure at least one strategy type is selected
    if (newTypes.length === 0) {
      return; // Don't allow deselecting all strategy types
    }
    
    updateConfiguration({ STRATEGY_TYPES: newTypes });
  };

  const handleOptionChange = (option: keyof AnalysisConfigType, checked: boolean) => {
    updateConfiguration({ [option]: checked });
  };

  const handleYearsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value);
    const error = validateYears(value);
    
    setFormErrors(prev => ({ ...prev, YEARS: error }));
    updateConfiguration({ YEARS: value });
  };

  const handleMinimumChange = (field: keyof AnalysisConfigType['MINIMUMS'], value: number) => {
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
    const preset = DEFAULT_PRESETS.find(p => p.name === presetName);
    if (preset) {
      // Preserve the current TICKER value when loading a preset
      const currentTicker = parameterTesting.configuration.TICKER;
      updateConfiguration({
        ...preset.config,
        TICKER: currentTicker, // Keep current ticker
        MINIMUMS: {
          ...parameterTesting.configuration.MINIMUMS,
          ...preset.config.MINIMUMS,
        },
      });
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
    const hasErrors = Object.values(formErrors).some(error => error !== undefined);
    const ticker = parameterTesting.configuration.TICKER;
    const tickerValue = Array.isArray(ticker) ? ticker.join(', ') : ticker;
    const hasRequiredFields = tickerValue.trim() !== '';
    return !hasErrors && hasRequiredFields;
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
            >
              <option value="">Choose a preset...</option>
              {DEFAULT_PRESETS.map((preset) => (
                <option key={preset.name} value={preset.name}>
                  {preset.name}
                </option>
              ))}
            </select>
            <div id="preset-help" className="form-text">Quick configuration templates</div>
          </div>

          {/* Ticker Input - Full Width */}
          <div className="col-12">
            <label htmlFor="ticker-input" className="form-label">
              <Icon icon={icons.search} className="me-1" />
              Ticker Symbol(s) <span className="text-danger">*</span>
            </label>
            <input
              type="text"
              className={`form-control ${formErrors.TICKER ? 'is-invalid' : ''}`}
              id="ticker-input"
              placeholder="e.g., AAPL, GOOGL, MSFT"
              value={Array.isArray(parameterTesting.configuration.TICKER) 
                ? parameterTesting.configuration.TICKER.join(', ') 
                : parameterTesting.configuration.TICKER}
              onChange={handleTickerChange}
              aria-describedby="ticker-help"
              aria-required="true"
              aria-invalid={!!formErrors.TICKER}
            />
            {formErrors.TICKER && (
              <div className="invalid-feedback" role="alert">{formErrors.TICKER}</div>
            )}
            <div id="ticker-help" className="form-text">Comma-separated list of ticker symbols</div>
          </div>

          <div className="col-md-3">
            <label htmlFor="windows-input" className="form-label">
              <Icon icon={icons.calculator} className="me-1" />
              Windows
            </label>
            <input
              type="number"
              className={`form-control ${formErrors.WINDOWS ? 'is-invalid' : ''}`}
              id="windows-input"
              value={parameterTesting.configuration.WINDOWS}
              min="1"
              max="50"
              onChange={handleWindowsChange}
              aria-describedby="windows-help"
              aria-invalid={!!formErrors.WINDOWS}
            />
            {formErrors.WINDOWS && (
              <div className="invalid-feedback" role="alert">{formErrors.WINDOWS}</div>
            )}
            <div id="windows-help" className="form-text">Number of window combinations (1-50)</div>
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
            <div className="d-flex gap-3">
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="sma-checkbox"
                  checked={parameterTesting.configuration.STRATEGY_TYPES.includes('SMA')}
                  onChange={(e) => handleStrategyTypeChange('SMA', e.target.checked)}
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
                  checked={parameterTesting.configuration.STRATEGY_TYPES.includes('EMA')}
                  onChange={(e) => handleStrategyTypeChange('EMA', e.target.checked)}
                />
                <label className="form-check-label" htmlFor="ema-checkbox">
                  EMA (Exponential Moving Average)
                </label>
              </div>
            </div>
          </div>

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
                    onChange={(e) => handleOptionChange('USE_CURRENT', e.target.checked)}
                  />
                  <label className="form-check-label" htmlFor="use-current-checkbox">
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
                    onChange={(e) => handleOptionChange('REFRESH', e.target.checked)}
                  />
                  <label className="form-check-label" htmlFor="refresh-checkbox">
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
                    onChange={(e) => handleOptionChange('USE_HOURLY', e.target.checked)}
                  />
                  <label className="form-check-label" htmlFor="use-hourly-checkbox">
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
                    onChange={(e) => handleOptionChange('USE_SCANNER', e.target.checked)}
                  />
                  <label className="form-check-label" htmlFor="use-scanner-checkbox">
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
              onClick={() => setShowAdvanced(!showAdvanced)}
              aria-expanded={showAdvanced}
              aria-controls="advanced-configuration"
            >
              <Icon icon={showAdvanced ? icons.chevronUp : icons.chevronDown} className="me-1" />
              Advanced Configuration
            </button>
          </div>

          {/* Advanced Configuration (Collapsible) */}
          {showAdvanced && (
            <div className="col-12" id="advanced-configuration">
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
                          onChange={(e) => handleOptionChange('USE_YEARS', e.target.checked)}
                        />
                        <label className="form-check-label" htmlFor="use-years-checkbox">
                          Use Years Limit
                        </label>
                      </div>
                      {parameterTesting.configuration.USE_YEARS && (
                        <input
                          type="number"
                          className={`form-control ${formErrors.YEARS ? 'is-invalid' : ''}`}
                          placeholder="Years"
                          value={parameterTesting.configuration.YEARS}
                          min="1"
                          max="50"
                          onChange={handleYearsChange}
                        />
                      )}
                      {formErrors.YEARS && (
                        <div className="invalid-feedback">{formErrors.YEARS}</div>
                      )}
                    </div>

                    {/* Additional Options */}
                    <div className="col-md-6">
                      <div className="form-check mb-2">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          id="use-synthetic-checkbox"
                          checked={parameterTesting.configuration.USE_SYNTHETIC}
                          onChange={(e) => handleOptionChange('USE_SYNTHETIC', e.target.checked)}
                        />
                        <label className="form-check-label" htmlFor="use-synthetic-checkbox">
                          Use Synthetic Data
                        </label>
                      </div>
                      <div className="form-check">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          id="use-gbm-checkbox"
                          checked={parameterTesting.configuration.USE_GBM}
                          onChange={(e) => handleOptionChange('USE_GBM', e.target.checked)}
                        />
                        <label className="form-check-label" htmlFor="use-gbm-checkbox">
                          Use GBM (Geometric Brownian Motion)
                        </label>
                      </div>
                    </div>

                    {/* Minimums Configuration */}
                    <div className="col-12">
                      <label className="form-label fw-bold">Minimum Thresholds</label>
                      <div className="row g-2">
                        <div className="col-md-2">
                          <label htmlFor="min-win-rate" className="form-label small">Win Rate %</label>
                          <input
                            type="number"
                            className="form-control form-control-sm"
                            id="min-win-rate"
                            value={parameterTesting.configuration.MINIMUMS.WIN_RATE}
                            min="0"
                            max="100"
                            onChange={(e) => handleMinimumChange('WIN_RATE', parseFloat(e.target.value))}
                          />
                        </div>
                        <div className="col-md-2">
                          <label htmlFor="min-trades" className="form-label small">Trades</label>
                          <input
                            type="number"
                            className="form-control form-control-sm"
                            id="min-trades"
                            value={parameterTesting.configuration.MINIMUMS.TRADES}
                            min="0"
                            onChange={(e) => handleMinimumChange('TRADES', parseInt(e.target.value))}
                          />
                        </div>
                        <div className="col-md-3">
                          <label htmlFor="min-expectancy" className="form-label small">Expectancy per Trade</label>
                          <input
                            type="number"
                            className="form-control form-control-sm"
                            id="min-expectancy"
                            value={parameterTesting.configuration.MINIMUMS.EXPECTANCY_PER_TRADE}
                            step="0.01"
                            onChange={(e) => handleMinimumChange('EXPECTANCY_PER_TRADE', parseFloat(e.target.value))}
                          />
                        </div>
                        <div className="col-md-2">
                          <label htmlFor="min-profit-factor" className="form-label small">Profit Factor</label>
                          <input
                            type="number"
                            className="form-control form-control-sm"
                            id="min-profit-factor"
                            value={parameterTesting.configuration.MINIMUMS.PROFIT_FACTOR}
                            step="0.1"
                            min="0"
                            onChange={(e) => handleMinimumChange('PROFIT_FACTOR', parseFloat(e.target.value))}
                          />
                        </div>
                        <div className="col-md-3">
                          <label htmlFor="min-sortino-ratio" className="form-label small">Sortino Ratio</label>
                          <input
                            type="number"
                            className="form-control form-control-sm"
                            id="min-sortino-ratio"
                            value={parameterTesting.configuration.MINIMUMS.SORTINO_RATIO}
                            step="0.1"
                            onChange={(e) => handleMinimumChange('SORTINO_RATIO', parseFloat(e.target.value))}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Sorting Configuration */}
                    <div className="col-md-6">
                      <label htmlFor="sort-by-select" className="form-label">Sort By</label>
                      <select
                        className="form-select"
                        id="sort-by-select"
                        value={parameterTesting.configuration.SORT_BY}
                        onChange={handleSortByChange}
                      >
                        <option value="Expectancy per Trade">Expectancy per Trade</option>
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
                            onChange={() => updateConfiguration({ SORT_ASC: false })}
                          />
                          <label className="form-check-label" htmlFor="sort-desc">
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
                            onChange={() => updateConfiguration({ SORT_ASC: true })}
                          />
                          <label className="form-check-label" htmlFor="sort-asc">
                            Ascending (Low to High)
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

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
              aria-describedby={!isFormValid() ? "validation-error" : undefined}
            >
              {isAnalyzing ? (
                <>
                  <Icon icon={icons.loading} className="me-2 fa-spin" aria-hidden="true" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Icon icon={icons.parameterTesting} className="me-2" aria-hidden="true" />
                  Run Analysis
                </>
              )}
            </button>
            {!isFormValid() && (
              <div id="validation-error" className="form-text text-danger" role="alert">
                Please fix validation errors and ensure all required fields are filled.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
});

export default AnalysisConfiguration;
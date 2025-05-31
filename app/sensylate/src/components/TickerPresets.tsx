import React, { useEffect, useState } from 'react';
import Icon from './Icon';
import { icons } from '../utils/icons';

interface TickerPresetsProps {
  onTickersChange: (tickers: string) => void;
  currentTickers: string;
}

interface TickerLists {
  [key: string]: string[];
}

export const TickerPresets: React.FC<TickerPresetsProps> = ({ onTickersChange }) => {
  const [tickerLists, setTickerLists] = useState<TickerLists>({});
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadTickerLists();
  }, []);

  const loadTickerLists = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await fetch('http://127.0.0.1:8000/api/data/ticker-lists');
      
      if (!response.ok) {
        // For development/testing: use mock data if API fails
        if (response.status === 500 || response.status === 404) {
          console.warn('API error, using mock ticker lists for development');
          setTickerLists({
            crypto: ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"],
            indices: ["SPY", "QQQ", "DIA", "IWM", "VTI"],
            portfolio: ["AAPL", "GOOGL", "MSFT", "AMZN", "NVDA", "TSLA", "META"],
            scanner: ["MSTR", "COIN", "SQ", "PYPL", "SHOP"]
          });
          return;
        }
        throw new Error(`Failed to load ticker lists: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success' && data.ticker_lists) {
        setTickerLists(data.ticker_lists);
      } else {
        throw new Error('Invalid response format from ticker lists API');
      }
    } catch (err) {
      console.error('Error loading ticker lists:', err);
      setError('Failed to load ticker presets. Using manual input.');
      // For development: provide some default lists even on error
      setTickerLists({
        crypto: ["BTC-USD", "ETH-USD", "SOL-USD"],
        indices: ["SPY", "QQQ", "DIA"]
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePresetChange = (presetName: string) => {
    setSelectedPreset(presetName);
    
    if (presetName && tickerLists[presetName]) {
      const tickers = tickerLists[presetName].join(',');
      onTickersChange(tickers);
    } else {
      // Clear selection - don't change the current tickers
      setSelectedPreset('');
    }
  };

  const capitalize = (str: string): string => {
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  if (loading) {
    return (
      <div>
        <label className="form-label">
          <Icon icon={icons.list} className="me-1" />
          Ticker Presets
        </label>
        <select 
          className="form-select" 
          disabled
        >
          <option>Loading ticker lists...</option>
        </select>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <label className="form-label">
          <Icon icon={icons.list} className="me-1" />
          Ticker Presets
        </label>
        <select 
          className="form-select" 
          disabled
        >
          <option>Error loading presets</option>
        </select>
        <div className="form-text text-danger">{error}</div>
      </div>
    );
  }

  return (
    <div>
      <label htmlFor="ticker-preset" className="form-label">
        <Icon icon={icons.list} className="me-1" />
        Ticker Presets
      </label>
      <select
        id="ticker-preset"
        className="form-select"
        value={selectedPreset}
        onChange={(e) => handlePresetChange(e.target.value)}
        aria-describedby="ticker-preset-help"
      >
        <option value="">None Selected (Use Manual Input)</option>
        {Object.keys(tickerLists).map((listName) => (
          <option key={listName} value={listName}>
            {capitalize(listName)} ({tickerLists[listName].length} tickers)
          </option>
        ))}
      </select>
      <div id="ticker-preset-help" className="form-text">
        {selectedPreset ? (
          <>
            Loaded {capitalize(selectedPreset)} list with {tickerLists[selectedPreset].length} tickers. 
            You can edit the list in the text field below.
          </>
        ) : (
          'Select a preset list or enter tickers manually'
        )}
      </div>
    </div>
  );
};
import React, { createContext, useState, useContext, ReactNode } from 'react';
import {
  CSVData,
  ParameterTestingState,
  AnalysisConfiguration,
} from '../types';

interface AppContextType {
  selectedFile: string | null;
  setSelectedFile: (file: string | null) => void;
  viewMode: 'table' | 'text';
  setViewMode: (mode: 'table' | 'text') => void;
  csvData: CSVData | null;
  setCsvData: (data: CSVData | null) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  updateStatus: string | null;
  setUpdateStatus: (status: string | null) => void;
  currentView: 'csv-viewer' | 'parameter-testing' | 'position-sizing';
  setCurrentView: (
    view: 'csv-viewer' | 'parameter-testing' | 'position-sizing'
  ) => void;
  parameterTesting: ParameterTestingState;
  setParameterTesting: (state: ParameterTestingState) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

interface AppProviderProps {
  children: ReactNode;
}

const defaultConfiguration: AnalysisConfiguration = {
  TICKER: '',
  WINDOWS: 20,
  DIRECTION: 'Long',
  STRATEGY_TYPES: ['SMA'],
  USE_HOURLY: false,
  USE_YEARS: false,
  YEARS: 2,
  USE_SYNTHETIC: false,
  USE_CURRENT: true,
  USE_SCANNER: false,
  REFRESH: false,
  MINIMUMS: {
    WIN_RATE: 0, // Start with 0 to show all results
    TRADES: 1,
    EXPECTANCY_PER_TRADE: 0,
    PROFIT_FACTOR: 0,
    SORTINO_RATIO: 0,
  },
  SORT_BY: 'Expectancy per Trade',
  SORT_ASC: false,
  USE_GBM: false,
  async_execution: true,
};

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'text'>('table');
  const [csvData, setCsvData] = useState<CSVData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [updateStatus, setUpdateStatus] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<
    'csv-viewer' | 'parameter-testing' | 'position-sizing'
  >('csv-viewer');
  const [parameterTesting, setParameterTesting] =
    useState<ParameterTestingState>({
      configuration: defaultConfiguration,
      results: [],
      isAnalyzing: false,
      error: null,
      progress: 0,
      executionId: null,
    });

  return (
    <AppContext.Provider
      value={{
        selectedFile,
        setSelectedFile,
        viewMode,
        setViewMode,
        csvData,
        setCsvData,
        isLoading,
        setIsLoading,
        error,
        setError,
        updateStatus,
        setUpdateStatus,
        currentView,
        setCurrentView,
        parameterTesting,
        setParameterTesting,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

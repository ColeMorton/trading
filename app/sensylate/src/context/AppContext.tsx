import React, { createContext, useState, useContext, ReactNode } from 'react';
import { CSVData } from '../types';

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
}

const AppContext = createContext<AppContextType | undefined>(undefined);

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'text'>('table');
  const [csvData, setCsvData] = useState<CSVData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [updateStatus, setUpdateStatus] = useState<string | null>(null);

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
        setUpdateStatus
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
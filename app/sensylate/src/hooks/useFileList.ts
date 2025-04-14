import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { CSVFile } from '../types';
import { useAppContext } from '../context/AppContext';

/**
 * Hook to fetch the list of CSV files
 * @returns Array of CSV files
 */
export const useFileList = () => {
  const [files, setFiles] = useState<CSVFile[]>([]);
  const { setError, setIsLoading, setSelectedFile } = useAppContext();
  
  useEffect(() => {
    const fetchFiles = async () => {
      try {
        setIsLoading(true);
        const fileList = await api.getFileList();
        setFiles(fileList);
        
        // Check if DAILY.csv exists and select it by default
        const dailyFile = fileList.find(file => file.name === 'DAILY.csv');
        if (dailyFile) {
          setSelectedFile(dailyFile.path);
        }
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to load file list');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchFiles();
  }, [setError, setIsLoading, setSelectedFile]);
  
  return files;
};
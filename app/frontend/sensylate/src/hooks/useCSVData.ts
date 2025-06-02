import { useEffect } from 'react';
import { api } from '../services/serviceFactory';
import { useAppContext } from '../context/AppContext';

/**
 * Hook to fetch CSV data for a selected file
 * @param filePath Path to the CSV file
 */
export const useCSVData = (filePath: string | null) => {
  const { setCsvData, setError, setIsLoading } = useAppContext();
  
  useEffect(() => {
    if (!filePath) {
      setCsvData(null);
      return;
    }
    
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await api.getCSVData(filePath);
        setCsvData(data);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to load CSV data');
        setCsvData(null);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [filePath, setCsvData, setError, setIsLoading]);
};
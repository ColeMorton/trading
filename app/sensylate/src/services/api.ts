import axios from 'axios';
import { CSVFile, CSVData, UpdateStatus } from '../types';

// Simple in-memory cache for offline support
// In a real app, you'd use IndexedDB or another persistent storage
const cache = {
  fileList: null as CSVFile[] | null,
  csvData: new Map<string, CSVData>()
};

export const api = {
  getFileList: async (): Promise<CSVFile[]> => {
    try {
      // Try to fetch from network
      const response = await axios.get('/api/data/list/strategies');
      if (!response.data || !response.data.files) {
        throw new Error('Invalid response format');
      }
      
      // Filter for CSV files only and format them
      const files = response.data.files
        .filter((file: any) => file.path.endsWith('.csv'))
        .map((file: any) => ({
          path: file.path,
          name: file.path.split('/').pop()
        }))
        .sort((a: CSVFile, b: CSVFile) => a.name.localeCompare(b.name));
      
      // Save to cache for offline use
      cache.fileList = files;
      
      return files;
    } catch (error) {
      console.log('Error fetching files from network, trying cache', error);
      
      // If network request fails, try to get from cache
      if (cache.fileList) {
        return cache.fileList;
      }
      
      // If no cached data, rethrow the error
      throw error;
    }
  },
  
  getCSVData: async (filePath: string): Promise<CSVData> => {
    try {
      // Try to fetch from network
      const response = await axios.get(`/api/data/csv/${filePath}`);
      if (!response.data || !response.data.data || !response.data.data.data) {
        throw new Error('Invalid response format');
      }
      
      const data = response.data.data.data;
      const csvData = {
        data,
        columns: Object.keys(data[0] || {})
      };
      
      // Save to cache for offline use
      cache.csvData.set(filePath, csvData);
      
      return csvData;
    } catch (error) {
      console.log('Error fetching CSV data from network, trying cache', error);
      
      // If network request fails, try to get from cache
      const cachedData = cache.csvData.get(filePath);
      if (cachedData) {
        return cachedData;
      }
      
      // If no cached data, rethrow the error
      throw error;
    }
  },
  
  updatePortfolio: async (fileName: string): Promise<UpdateStatus> => {
    // This operation requires network connectivity
    const response = await axios.post('/api/scripts/update-portfolio', {
      portfolio: fileName
    });
    return response.data;
  }
};
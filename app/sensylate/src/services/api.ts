import axios from 'axios';
import { CSVFile, CSVData, UpdateStatus } from '../types';

export const api = {
  getFileList: async (): Promise<CSVFile[]> => {
    const response = await axios.get('/api/data/list/strategies');
    if (!response.data || !response.data.files) {
      throw new Error('Invalid response format');
    }
    
    // Filter for CSV files only and format them
    return response.data.files
      .filter((file: any) => file.path.endsWith('.csv'))
      .map((file: any) => ({
        path: file.path,
        name: file.path.split('/').pop()
      }))
      .sort((a: CSVFile, b: CSVFile) => a.name.localeCompare(b.name));
  },
  
  getCSVData: async (filePath: string): Promise<CSVData> => {
    const response = await axios.get(`/api/data/csv/${filePath}`);
    if (!response.data || !response.data.data || !response.data.data.data) {
      throw new Error('Invalid response format');
    }
    
    const data = response.data.data.data;
    return {
      data,
      columns: Object.keys(data[0] || {})
    };
  },
  
  updatePortfolio: async (fileName: string): Promise<UpdateStatus> => {
    const response = await axios.post('/api/scripts/update-portfolio', {
      portfolio: fileName
    });
    return response.data;
  }
};
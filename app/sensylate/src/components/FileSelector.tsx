import React from 'react';
import { useFileList } from '../hooks/useFileList';
import { useAppContext } from '../context/AppContext';
import { useCSVData } from '../hooks/useCSVData';

/**
 * Component for selecting a CSV file from the dropdown
 */
const FileSelector: React.FC = () => {
  const files = useFileList();
  const { selectedFile, setSelectedFile } = useAppContext();
  
  // This hook will fetch CSV data when selectedFile changes
  useCSVData(selectedFile);
  
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedFile(e.target.value || null);
  };
  
  return (
    <div className="flex-grow">
      <label htmlFor="file-selector" className="block text-sm font-medium text-gray-700 mb-2">
        Select CSV File:
      </label>
      <select
        id="file-selector"
        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
        value={selectedFile || ''}
        onChange={handleChange}
      >
        <option value="">Select a file...</option>
        {files.map(file => (
          <option key={file.path} value={file.path}>
            {file.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default FileSelector;
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
      <label htmlFor="file-selector" className="block text-sm font-medium mb-2" style={{ color: 'var(--bs-body-color)' }}>
        Select CSV File:
      </label>
      <select
        id="file-selector"
        className="form-control block w-full"
        style={{
          backgroundColor: 'var(--bs-input-bg)',
          color: 'var(--bs-input-color)',
          border: '1px solid var(--bs-input-border-color)',
          borderRadius: '0.375rem',
          padding: '0.375rem 0.75rem'
        }}
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
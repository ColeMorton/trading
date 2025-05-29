import React from 'react';
import { useFileList } from '../hooks/useFileList';
import { useAppContext } from '../context/AppContext';
import { useCSVData } from '../hooks/useCSVData';
import Icon from './Icon';
import { icons } from '../utils/icons';

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
    <div className="flex-grow-1">
      <label htmlFor="file-selector" className="form-label d-flex align-items-center">
        <Icon icon={icons.folder} className="me-2" />
        Select CSV File:
      </label>
      <div className="input-group">
        <span className="input-group-text">
          <Icon icon={icons.file} />
        </span>
        <select
          id="file-selector"
          className="form-select"
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
    </div>
  );
};

export default FileSelector;
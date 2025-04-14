import React from 'react';
import { useAppContext } from '../context/AppContext';

/**
 * Component to display information about the selected file
 */
const FileInfo: React.FC = () => {
  const { csvData, selectedFile } = useAppContext();
  
  if (!csvData || !selectedFile) {
    return null;
  }
  
  const fileName = selectedFile.split('/').pop();
  
  return (
    <div className="mb-4 p-3 bg-white rounded shadow-sm">
      <p><strong>File:</strong> {fileName}</p>
      <p><strong>Rows:</strong> {csvData.data.length}</p>
      <p><strong>Columns:</strong> {csvData.columns.length}</p>
    </div>
  );
};

export default FileInfo;
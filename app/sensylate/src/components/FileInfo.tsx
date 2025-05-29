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
    <div className="card mb-4">
      <div className="card-header">
        <h5 className="card-title mb-0">File Information</h5>
      </div>
      <div className="card-body">
        <p><strong>File:</strong> {fileName}</p>
        <p><strong>Rows:</strong> {csvData.data.length}</p>
        <p><strong>Columns:</strong> {csvData.columns.length}</p>
      </div>
    </div>
  );
};

export default FileInfo;
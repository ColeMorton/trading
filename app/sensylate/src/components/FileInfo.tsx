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
    <div className="mb-6 rounded-lg border" style={{ 
      backgroundColor: 'var(--bs-card-bg)', 
      borderColor: 'var(--bs-card-border-color)' 
    }}>
      <div className="border-b px-4 py-3" style={{ 
        backgroundColor: 'var(--bs-card-cap-bg)', 
        borderColor: 'var(--bs-card-border-color)' 
      }}>
        <h5 className="mb-0 font-bold" style={{ color: 'var(--bs-body-color)' }}>File Information</h5>
      </div>
      <div className="p-4" style={{ color: 'var(--bs-body-color)' }}>
        <p><strong>File:</strong> {fileName}</p>
        <p><strong>Rows:</strong> {csvData.data.length}</p>
        <p><strong>Columns:</strong> {csvData.columns.length}</p>
      </div>
    </div>
  );
};

export default FileInfo;
import React from 'react';
import { useAppContext } from '../context/AppContext';
import Icon from './Icon';
import { icons } from '../utils/icons';

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
      <div className="card-header d-flex align-items-center">
        <Icon icon={icons.info} className="me-2" />
        <h5 className="card-title mb-0">File Information</h5>
      </div>
      <div className="card-body">
        <p>
          <Icon icon={icons.file} className="me-2 text-muted" />
          <strong>File:</strong> {fileName}
        </p>
        <p>
          <Icon icon={icons.table} className="me-2 text-muted" />
          <strong>Rows:</strong> {csvData.data.length}
        </p>
        <p>
          <Icon icon={icons.columns} className="me-2 text-muted" />
          <strong>Columns:</strong> {csvData.columns.length}
        </p>
      </div>
    </div>
  );
};

export default FileInfo;

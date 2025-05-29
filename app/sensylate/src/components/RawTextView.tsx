import React, { useMemo } from 'react';
import { useAppContext } from '../context/AppContext';
import { convertToRawText } from '../utils/csvUtils';

/**
 * Component to display CSV data as raw text
 */
const RawTextView: React.FC = () => {
  const { csvData, viewMode } = useAppContext();
  
  const rawText = useMemo(() => {
    if (!csvData) return '';
    return convertToRawText(csvData.data, csvData.columns);
  }, [csvData]);
  
  if (viewMode !== 'text' || !csvData) {
    return null;
  }
  
  return (
    <div className="card mb-4">
      <div className="card-header">
        <h5 className="card-title mb-0">Raw Data View</h5>
      </div>
      <div className="card-body">
        <textarea
          id="csv-text"
          value={rawText}
          readOnly
          className="form-control"
        ></textarea>
      </div>
    </div>
  );
};

export default RawTextView;
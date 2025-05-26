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
    <div className="mb-6 rounded-lg border overflow-hidden" style={{ 
      backgroundColor: 'var(--bs-card-bg)', 
      borderColor: 'var(--bs-card-border-color)' 
    }}>
      <div className="border-b px-4 py-3" style={{ 
        backgroundColor: 'var(--bs-card-cap-bg)', 
        borderColor: 'var(--bs-card-border-color)' 
      }}>
        <h5 className="mb-0 font-bold" style={{ color: 'var(--bs-body-color)' }}>Raw Data View</h5>
      </div>
      <div className="p-4">
        <textarea
          id="csv-text"
          value={rawText}
          readOnly
        ></textarea>
      </div>
    </div>
  );
};

export default RawTextView;
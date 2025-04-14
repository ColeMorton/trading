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
    <div className="overflow-x-auto bg-white rounded-lg shadow-lg p-4">
      <textarea
        id="csv-text"
        className="w-full h-[70vh] font-mono text-sm border border-gray-300 rounded-md p-2"
        value={rawText}
        readOnly
      ></textarea>
    </div>
  );
};

export default RawTextView;
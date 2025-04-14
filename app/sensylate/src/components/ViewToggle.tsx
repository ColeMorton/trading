import React from 'react';
import { useAppContext } from '../context/AppContext';

/**
 * Component to toggle between table and text views
 */
const ViewToggle: React.FC = () => {
  const { viewMode, setViewMode, csvData } = useAppContext();
  
  if (!csvData) {
    return null;
  }
  
  return (
    <div className="mb-4 p-3 bg-white rounded shadow-sm">
      <div className="flex space-x-2">
        <button 
          onClick={() => setViewMode('table')}
          className={`px-4 py-2 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
            viewMode === 'table' 
              ? 'bg-indigo-600 text-white' 
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Table View
        </button>
        <button 
          onClick={() => setViewMode('text')}
          className={`px-4 py-2 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
            viewMode === 'text' 
              ? 'bg-indigo-600 text-white' 
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Raw Text View
        </button>
      </div>
    </div>
  );
};

export default ViewToggle;
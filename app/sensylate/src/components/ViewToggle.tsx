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
    <div className="mb-6 rounded-lg border" style={{ 
      backgroundColor: 'var(--bs-card-bg)', 
      borderColor: 'var(--bs-card-border-color)' 
    }}>
      <div className="border-b px-4 py-3" style={{ 
        backgroundColor: 'var(--bs-card-cap-bg)', 
        borderColor: 'var(--bs-card-border-color)' 
      }}>
        <h5 className="mb-0 font-bold" style={{ color: 'var(--bs-body-color)' }}>View Options</h5>
      </div>
      <div className="p-4">
        <div className="flex space-x-2">
          <button 
            onClick={() => setViewMode('table')}
            className="px-4 py-2 rounded-md"
            style={{
              backgroundColor: viewMode === 'table' ? 'var(--bs-primary)' : 'rgba(255, 255, 255, 0.1)',
              color: viewMode === 'table' ? 'white' : 'var(--bs-body-color)',
              border: '1px solid var(--bs-border-color)'
            }}
          >
            Table View
          </button>
          <button 
            onClick={() => setViewMode('text')}
            className="px-4 py-2 rounded-md"
            style={{
              backgroundColor: viewMode === 'text' ? 'var(--bs-primary)' : 'rgba(255, 255, 255, 0.1)',
              color: viewMode === 'text' ? 'white' : 'var(--bs-body-color)',
              border: '1px solid var(--bs-border-color)'
            }}
          >
            Raw Text View
          </button>
        </div>
      </div>
    </div>
  );
};

export default ViewToggle;
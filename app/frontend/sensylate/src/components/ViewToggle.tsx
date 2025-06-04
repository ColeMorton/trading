import React from 'react';
import { useAppContext } from '../context/AppContext';
import Icon from './Icon';
import { icons } from '../utils/icons';

/**
 * Component to toggle between table and text views
 */
const ViewToggle: React.FC = () => {
  const { viewMode, setViewMode, csvData } = useAppContext();

  if (!csvData) {
    return null;
  }

  return (
    <div className="card mb-4">
      <div className="card-header">
        <h5 className="card-title mb-0">View Options</h5>
      </div>
      <div className="card-body">
        <div className="btn-group" role="group" aria-label="View toggle">
          <button
            onClick={() => setViewMode('table')}
            className={`btn ${
              viewMode === 'table' ? 'btn-primary' : 'btn-outline-secondary'
            }`}
          >
            <Icon icon={icons.table} className="me-2" />
            Table View
          </button>
          <button
            onClick={() => setViewMode('text')}
            className={`btn ${
              viewMode === 'text' ? 'btn-primary' : 'btn-outline-secondary'
            }`}
          >
            <Icon icon={icons.textView} className="me-2" />
            Raw Text View
          </button>
        </div>
      </div>
    </div>
  );
};

export default ViewToggle;

import React from 'react';
import { useAppContext } from '../context/AppContext';

/**
 * Component to display a loading spinner
 */
const LoadingIndicator: React.FC = () => {
  const { isLoading } = useAppContext();
  
  if (!isLoading) {
    return null;
  }
  
  return (
    <div className="d-flex align-items-center justify-content-center p-4">
      <div className="spinner-border text-primary me-3" role="status">
        <span className="visually-hidden">Loading...</span>
      </div>
      <span>Loading CSV data...</span>
    </div>
  );
};

export default LoadingIndicator;
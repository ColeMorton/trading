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
    <div className="flex items-center justify-center p-6">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      <span className="ml-3">Loading CSV data...</span>
    </div>
  );
};

export default LoadingIndicator;
import React from 'react';
import { useAppContext } from '../context/AppContext';
import Icon from './Icon';
import { icons } from '../utils/icons';

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
      <Icon icon={icons.loading} spin size="2x" className="text-primary me-3" />
      <span>Loading CSV data...</span>
    </div>
  );
};

export default LoadingIndicator;

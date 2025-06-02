import React from 'react';
import { useAppContext } from '../context/AppContext';
import Icon from './Icon';
import { icons } from '../utils/icons';

/**
 * Component to display error messages
 */
const ErrorMessage: React.FC = () => {
  const { error, setError } = useAppContext();
  
  if (!error) {
    return null;
  }
  
  return (
    <div className="alert alert-danger alert-dismissible d-flex align-items-center" role="alert">
      <Icon icon={icons.error} className="me-2 flex-shrink-0" />
      <div className="flex-grow-1">{error}</div>
      <button 
        type="button"
        className="btn-close"
        aria-label="Close"
        onClick={() => setError(null)}
      ></button>
    </div>
  );
};

export default ErrorMessage;
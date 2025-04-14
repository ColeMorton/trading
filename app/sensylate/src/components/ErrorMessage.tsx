import React from 'react';
import { useAppContext } from '../context/AppContext';

/**
 * Component to display error messages
 */
const ErrorMessage: React.FC = () => {
  const { error, setError } = useAppContext();
  
  if (!error) {
    return null;
  }
  
  return (
    <div className="p-4 mb-4 text-red-700 bg-red-100 rounded-lg flex justify-between items-center">
      <div>{error}</div>
      <button 
        onClick={() => setError(null)}
        className="ml-4 text-red-700 hover:text-red-900"
      >
        ✕
      </button>
    </div>
  );
};

export default ErrorMessage;
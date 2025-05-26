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
    <div className="p-4 mb-4 rounded-lg flex justify-between items-center" role="alert" style={{
      backgroundColor: 'var(--bs-danger)',
      color: 'white'
    }}>
      <div className="flex items-center">
        <svg className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
        {error}
      </div>
      <button 
        onClick={() => setError(null)}
        className="ml-4 hover:opacity-75"
        style={{ color: 'white' }}
        aria-label="Close error message"
      >
        ✕
      </button>
    </div>
  );
};

export default ErrorMessage;
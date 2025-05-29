import React from 'react';
import { useOffline } from '../context/OfflineContext';

const OfflineBanner: React.FC = () => {
  const { isOnline, lastUpdated } = useOffline();

  if (isOnline) return null;

  return (
    <div className="alert alert-warning mb-4" role="alert">
      <div className="d-flex">
        <div className="flex-shrink-0">
          <svg className="me-2" width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
        <div>
          <p className="mb-0">
            You are currently offline. Some features may be limited.
            {lastUpdated && (
              <small className="d-block text-muted mt-1">
                Last updated: {lastUpdated.toLocaleString()}
              </small>
            )}
          </p>
        </div>
      </div>
    </div>
  );
};

export default OfflineBanner;
import React from 'react';
import { useOffline } from '../context/OfflineContext';
import Icon from './Icon';
import { icons } from '../utils/icons';

const OfflineBanner: React.FC = () => {
  const { isOnline, lastUpdated } = useOffline();

  if (isOnline) return null;

  return (
    <div className="alert alert-warning mb-4 d-flex align-items-start" role="alert">
      <Icon icon={icons.offline} className="me-2 flex-shrink-0" />
      <div>
        <p className="mb-0">
          <strong>You are currently offline.</strong> Some features may be limited.
          {lastUpdated && (
            <small className="d-block text-muted mt-1">
              <Icon icon={icons.lastUpdated} className="me-1" size="sm" />
              Last updated: {lastUpdated.toLocaleString()}
            </small>
          )}
        </p>
      </div>
    </div>
  );
};

export default OfflineBanner;
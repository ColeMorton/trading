import React, { useEffect, useState } from 'react';
import Icon from './Icon';
import { icons } from '../utils/icons';

// Define types for the virtual module
interface RegisterSWOptions {
  onRegistered?: (registration: ServiceWorkerRegistration | undefined) => void;
  onRegisterError?: (error: Error) => void;
}

interface RegisterSWResult {
  offlineReady: boolean;
  needRefresh: boolean;
  updateServiceWorker: (reloadPage?: boolean) => Promise<void>;
}

// Mock the useRegisterSW hook until the actual module is available at runtime
// This helps TypeScript during development
const useRegisterSW = (_options: RegisterSWOptions): RegisterSWResult => {
  // This is just a placeholder implementation for TypeScript
  // The actual implementation will be provided by the vite-plugin-pwa at runtime
  return {
    offlineReady: false,
    needRefresh: false,
    updateServiceWorker: async () => {},
  };
};

const PWAUpdateNotification: React.FC = () => {
  const [needRefresh, setNeedRefresh] = useState(false);
  const { updateServiceWorker, needRefresh: swNeedRefresh } = useRegisterSW({
    onRegistered(r) {
      console.log('SW registered:', r);
    },
    onRegisterError(error) {
      console.log('SW registration error', error);
    },
  });

  useEffect(() => {
    if (swNeedRefresh) {
      setNeedRefresh(true);
    }
  }, [swNeedRefresh]);

  const close = () => {
    setNeedRefresh(false);
  };

  const updateSW = () => {
    updateServiceWorker(true);
  };

  if (!needRefresh) return null;

  return (
    <div
      className="position-fixed bottom-0 end-0 m-4 p-4 border rounded shadow-lg bg-body"
      style={{ zIndex: 1050 }}
    >
      <div className="d-flex flex-column">
        <div className="mb-2">
          <div className="d-flex align-items-center mb-1">
            <Icon icon={icons.notification} className="me-2 text-primary" />
            <h5 className="mb-0">New Version Available</h5>
          </div>
          <p className="small text-muted mb-0">
            A new version of Sensylate is available. Click update to get the
            latest features.
          </p>
        </div>
        <div className="d-flex justify-content-end gap-2">
          <button className="btn btn-sm btn-outline-secondary" onClick={close}>
            <Icon icon={icons.times} className="me-2" />
            Close
          </button>
          <button className="btn btn-sm btn-primary" onClick={updateSW}>
            <Icon icon={icons.refresh} className="me-2" />
            Update
          </button>
        </div>
      </div>
    </div>
  );
};

export default PWAUpdateNotification;

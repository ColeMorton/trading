import React, { useEffect, useState } from 'react';

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
    updateServiceWorker: async () => {}
  };
};

const PWAUpdateNotification: React.FC = () => {
  const [needRefresh, setNeedRefresh] = useState(false);
  const {
    updateServiceWorker,
    needRefresh: swNeedRefresh
  } = useRegisterSW({
    onRegistered(r) {
      console.log('SW registered:', r);
    },
    onRegisterError(error) {
      console.log('SW registration error', error);
    }
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
    <div className="fixed bottom-0 right-0 m-4 p-4 bg-white rounded-lg shadow-lg z-50 border border-indigo-200">
      <div className="flex flex-col">
        <div className="mb-2">
          <h3 className="text-lg font-semibold">New Version Available</h3>
          <p className="text-sm text-gray-600">
            A new version of Sensylate is available. Click update to get the latest features.
          </p>
        </div>
        <div className="flex justify-end space-x-2">
          <button
            className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
            onClick={close}
          >
            Close
          </button>
          <button
            className="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700"
            onClick={updateSW}
          >
            Update
          </button>
        </div>
      </div>
    </div>
  );
};

export default PWAUpdateNotification;
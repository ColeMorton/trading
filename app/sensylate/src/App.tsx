import React from 'react';
import { AppProvider } from './context/AppContext';
import { OfflineProvider } from './context/OfflineContext';
import FileSelector from './components/FileSelector';
import FileInfo from './components/FileInfo';
import LoadingIndicator from './components/LoadingIndicator';
import ErrorMessage from './components/ErrorMessage';
import ViewToggle from './components/ViewToggle';
import DataTable from './components/DataTable';
import RawTextView from './components/RawTextView';
import UpdateButton from './components/UpdateButton';
import OfflineBanner from './components/OfflineBanner';
import PWAUpdateNotification from './components/PWAUpdateNotification';
import InstallPrompt from './components/InstallPrompt';

const App: React.FC = () => {
  return (
    <OfflineProvider>
      <AppProvider>
        <div className="min-vh-100">
          <a href="#main-content" className="skip-link">Skip to main content</a>
          
          <main id="main-content" className="container-fluid px-4 pb-4">
            <OfflineBanner />
            <ErrorMessage />
            
            {/* Control Panel Card */}
            <div className="card mb-4">
              <div className="card-header">
                <h5 className="card-title mb-0">Control Panel</h5>
              </div>
              <div className="card-body">
                <div className="row g-3">
                  <div className="col-md-12">
                    <FileSelector />
                  </div>
                  <div className="col-md-12">
                    <UpdateButton />
                  </div>
                </div>
              </div>
            </div>
            
            <FileInfo />
            <ViewToggle />
            <LoadingIndicator />
            
            <DataTable />
            <RawTextView />
            
            <PWAUpdateNotification />
            <InstallPrompt />
          </main>
        </div>
      </AppProvider>
    </OfflineProvider>
  );
};

export default App;
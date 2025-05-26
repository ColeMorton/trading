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
        <div className="min-h-screen" style={{ backgroundColor: 'var(--bs-body-bg)' }}>
          <a href="#main-content" className="skip-link">Skip to main content</a>
          
          <header className="mb-8 p-6">
            <h1 className="text-4xl font-bold" style={{ color: 'var(--bs-body-color)' }}>Sensylate</h1>
            <p style={{ color: 'var(--bs-secondary-color)' }}>Sensitivity analysis meets portfolio simulation and strategy creation</p>
          </header>
          
          <main id="main-content" className="container-fluid px-6 pb-6">
            <OfflineBanner />
            <ErrorMessage />
            
            {/* Control Panel Card */}
            <div className="mb-6 rounded-lg border" style={{ 
              backgroundColor: 'var(--bs-card-bg)', 
              borderColor: 'var(--bs-card-border-color)' 
            }}>
              <div className="border-b px-4 py-3" style={{ 
                backgroundColor: 'var(--bs-card-cap-bg)', 
                borderColor: 'var(--bs-card-border-color)' 
              }}>
                <h5 className="mb-0 font-bold" style={{ color: 'var(--bs-body-color)' }}>Control Panel</h5>
              </div>
              <div className="p-4">
                <div className="flex flex-col md:flex-row gap-4">
                  <FileSelector />
                  <UpdateButton />
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
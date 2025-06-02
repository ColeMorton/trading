import React from 'react';
import { AppProvider } from './context/AppContext';
import { OfflineProvider } from './context/OfflineContext';
import { ApolloProvider } from './providers/ApolloProvider';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
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
import ParameterTestingContainer from './components/ParameterTestingContainer';
import ErrorBoundary from './components/ErrorBoundary';
import Icon from './components/Icon';
import { icons } from './utils/icons';
import { useAppContext } from './context/AppContext';
import { isUsingGraphQL } from './services/serviceFactory';

const AppContent: React.FC = () => {
  const { currentView } = useAppContext();

  return (
    <div className="min-vh-100 d-flex flex-column">
      <a href="#main-content" className="skip-link">
        <Icon icon={icons.skipLink} className="me-2" />
        Skip to main content
      </a>
      
      <Navbar />
      
      <main id="main-content" className="container-fluid px-4 py-4 flex-fill">
        <OfflineBanner />
        <ErrorMessage />
        
        {currentView === 'csv-viewer' && (
          <>
            {/* Control Panel Card */}
            <div className="card mb-4">
              <div className="card-header d-flex align-items-center">
                <Icon icon={icons.settings} className="me-2" />
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
          </>
        )}

        {currentView === 'parameter-testing' && (
          <ErrorBoundary>
            <ParameterTestingContainer />
          </ErrorBoundary>
        )}
        
        <PWAUpdateNotification />
        <InstallPrompt />
      </main>
      
      <Footer />
    </div>
  );
};

const App: React.FC = () => {
  // Conditionally wrap with Apollo Provider when using GraphQL
  const content = (
    <OfflineProvider>
      <AppProvider>
        <AppContent />
      </AppProvider>
    </OfflineProvider>
  );

  // Only wrap with Apollo Provider if using GraphQL
  if (isUsingGraphQL()) {
    return <ApolloProvider>{content}</ApolloProvider>;
  }

  return content;
};

export default App;
import React from 'react';
import { AppProvider } from './context/AppContext';
import FileSelector from './components/FileSelector';
import FileInfo from './components/FileInfo';
import LoadingIndicator from './components/LoadingIndicator';
import ErrorMessage from './components/ErrorMessage';
import ViewToggle from './components/ViewToggle';
import DataTable from './components/DataTable';
import RawTextView from './components/RawTextView';
import UpdateButton from './components/UpdateButton';

const App: React.FC = () => {
  return (
    <AppProvider>
      <div className="min-h-screen bg-gray-100 p-6">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Sensylate</h1>
          <p className="text-gray-600">Sensitivity analysis meets portfolio simulation and strategy creation</p>
        </header>
        
        <ErrorMessage />
        
        <div className="mb-6 flex flex-col md:flex-row gap-4">
          <FileSelector />
          <UpdateButton />
        </div>
        
        <FileInfo />
        <ViewToggle />
        <LoadingIndicator />
        
        <DataTable />
        <RawTextView />
      </div>
    </AppProvider>
  );
};

export default App;
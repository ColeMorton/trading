import React from 'react';
import { useAppContext } from '../context/AppContext';
import { usePortfolioUpdate } from '../hooks/usePortfolioUpdate';

/**
 * Component for the update portfolio button with progress tracking
 */
const UpdateButton: React.FC = () => {
  const { selectedFile, setSelectedFile, setError } = useAppContext();
  
  // Refresh the CSV data when update completes
  const refreshData = () => {
    // The useCSVData hook will automatically refetch when selectedFile changes
    // To force a refresh without changing the file, we can toggle the selectedFile
    if (selectedFile) {
      const tempFile = selectedFile;
      setError(null);
      // Force a refresh by briefly setting to null and back
      setSelectedFile(null);
      setTimeout(() => {
        setSelectedFile(tempFile);
      }, 100);
    }
  };
  
  const { startUpdate, isUpdating, progress, updateStatus, error } = usePortfolioUpdate(refreshData);
  
  const handleClick = () => {
    if (!selectedFile) {
      setError('No file selected');
      return;
    }
    
    const fileName = selectedFile.split('/').pop();
    if (!fileName) {
      setError('Invalid file path');
      return;
    }
    
    startUpdate(fileName);
  };
  
  return (
    <div className="pt-6">
      <button
        disabled={!selectedFile || isUpdating}
        className="px-4 py-2 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
        style={{
          backgroundColor: 'var(--bs-primary)',
          color: 'white',
          border: '1px solid var(--bs-primary)'
        }}
        onClick={handleClick}
      >
        {isUpdating ? (
          <>
            <span className="animate-spin inline-block mr-2">↻</span> Updating...
          </>
        ) : (
          'Update'
        )}
      </button>
      
      {updateStatus && (
        <div className="mt-2 p-2 rounded" style={{
          backgroundColor: updateStatus.status === 'completed' ? 'var(--bs-success)' :
                         updateStatus.status === 'failed' ? 'var(--bs-danger)' :
                         'var(--bs-info)',
          color: 'white'
        }}>
          {updateStatus.status === 'completed' ? 'Update completed' :
           updateStatus.status === 'failed' ? `Update failed: ${updateStatus.error || 'Unknown error'}` :
           `Status: ${updateStatus.status} ${progress > 0 ? `(${progress}%)` : ''}`}
          
          {progress > 0 && updateStatus.status !== 'completed' && updateStatus.status !== 'failed' && (
            <div className="w-full rounded-full h-2.5 mt-2" style={{ backgroundColor: 'rgba(255, 255, 255, 0.3)' }}>
              <div
                className="h-2.5 rounded-full"
                style={{ 
                  backgroundColor: 'var(--bs-primary)',
                  width: `${progress}%` 
                }}
              ></div>
            </div>
          )}
        </div>
      )}
      
      {error && (
        <div className="mt-2 p-2 rounded" style={{ backgroundColor: 'var(--bs-danger)', color: 'white' }}>
          {error}
        </div>
      )}
    </div>
  );
};

export default UpdateButton;
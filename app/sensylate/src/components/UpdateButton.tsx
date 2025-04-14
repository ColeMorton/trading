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
        className="px-4 py-2 bg-indigo-600 text-white rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
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
        <div className={`mt-2 p-2 rounded ${
          updateStatus.status === 'completed' ? 'bg-green-100 text-green-800' :
          updateStatus.status === 'failed' ? 'bg-red-100 text-red-800' :
          'bg-blue-100 text-blue-800'
        }`}>
          {updateStatus.status === 'completed' ? 'Update completed' :
           updateStatus.status === 'failed' ? `Update failed: ${updateStatus.error || 'Unknown error'}` :
           `Status: ${updateStatus.status} ${progress > 0 ? `(${progress}%)` : ''}`}
          
          {progress > 0 && updateStatus.status !== 'completed' && updateStatus.status !== 'failed' && (
            <div className="w-full bg-gray-200 rounded-full h-2.5 mt-2">
              <div
                className="bg-indigo-600 h-2.5 rounded-full"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          )}
        </div>
      )}
      
      {error && (
        <div className="mt-2 p-2 rounded bg-red-100 text-red-800">
          {error}
        </div>
      )}
    </div>
  );
};

export default UpdateButton;
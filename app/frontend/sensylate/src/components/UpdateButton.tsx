import React from 'react';
import { useAppContext } from '../context/AppContext';
import { usePortfolioUpdate } from '../hooks/usePortfolioUpdate';
import Icon from './Icon';
import { icons } from '../utils/icons';

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

  const { startUpdate, isUpdating, progress, updateStatus, error } =
    usePortfolioUpdate(refreshData);

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
    <div className="pt-3">
      <button
        disabled={!selectedFile || isUpdating}
        className="btn btn-primary"
        onClick={handleClick}
      >
        {isUpdating ? (
          <>
            <Icon icon={icons.loading} spin className="me-2" />
            Updating...
          </>
        ) : (
          <>
            <Icon icon={icons.refresh} className="me-2" />
            Update
          </>
        )}
      </button>

      {updateStatus && (
        <div
          className={`alert mt-3 ${
            updateStatus.status === 'completed'
              ? 'alert-success'
              : updateStatus.status === 'failed'
                ? 'alert-danger'
                : 'alert-info'
          }`}
          role="alert"
        >
          {updateStatus.status === 'completed'
            ? 'Update completed'
            : updateStatus.status === 'failed'
              ? `Update failed: ${updateStatus.error || 'Unknown error'}`
              : `Status: ${updateStatus.status} ${
                  progress > 0 ? `(${progress}%)` : ''
                }`}

          {progress > 0 &&
            updateStatus.status !== 'completed' &&
            updateStatus.status !== 'failed' && (
              <div className="progress mt-2">
                <div
                  className="progress-bar"
                  role="progressbar"
                  style={{ width: `${progress}%` }}
                  aria-valuenow={progress}
                  aria-valuemin={0}
                  aria-valuemax={100}
                ></div>
              </div>
            )}
        </div>
      )}

      {error && (
        <div className="alert alert-danger mt-3" role="alert">
          {error}
        </div>
      )}
    </div>
  );
};

export default UpdateButton;

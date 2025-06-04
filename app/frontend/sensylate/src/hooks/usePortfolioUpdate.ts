import { useState, useEffect, useRef } from 'react';
import { api } from '../services/serviceFactory';
import { UpdateStatus } from '../types';

/**
 * Hook to handle portfolio updates with SSE for real-time progress
 * @param onUpdateComplete Optional callback when update completes
 */
export const usePortfolioUpdate = (onUpdateComplete?: () => void) => {
  const [updateStatus, setUpdateStatus] = useState<UpdateStatus | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState<boolean>(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Clean up event source on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const startUpdate = async (fileName: string) => {
    try {
      setIsUpdating(true);
      setError(null);

      const response = await api.updatePortfolio(fileName);
      setUpdateStatus(response);

      if (response.status === 'accepted' && response.execution_id) {
        // Set up SSE connection
        const eventSource = new EventSource(
          `/api/scripts/status-stream/${response.execution_id}`
        );
        eventSourceRef.current = eventSource;

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as UpdateStatus;
            setUpdateStatus(data);
            setProgress(data.progress || 0);

            if (data.status === 'completed') {
              setIsUpdating(false);
              eventSource.close();

              // Reload the current file to refresh data
              if (onUpdateComplete) {
                onUpdateComplete();
              }
            } else if (data.status === 'failed') {
              setError(data.error || 'Update failed');
              setIsUpdating(false);
              eventSource.close();
            }
          } catch (err) {
            setError('Failed to parse update status');
            setIsUpdating(false);
            eventSource.close();
          }
        };

        eventSource.onerror = () => {
          setError('Connection to update stream lost');
          setIsUpdating(false);
          eventSource.close();
        };
      } else {
        setError(response.message || 'Failed to start update');
        setIsUpdating(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start update');
      setIsUpdating(false);
    }
  };

  return {
    startUpdate,
    updateStatus,
    progress,
    error,
    isUpdating,
  };
};

import { useState, useCallback, useRef, useEffect } from 'react';
import { AnalysisConfiguration, AnalysisResult } from '../types';
import { maCrossApi, MACrossSyncResponse, MACrossAsyncResponse } from '../services/maCrossApi';

export interface UseParameterTestingReturn {
  analyze: (config: AnalysisConfiguration) => Promise<void>;
  results: AnalysisResult[];
  isAnalyzing: boolean;
  progress: number;
  error: string | null;
  executionId: string | null;
  clearResults: () => void;
  cancelAnalysis: () => void;
}

const POLLING_INTERVAL = 1000; // 1 second
const MAX_POLLING_ATTEMPTS = 600; // 10 minutes max

export const useParameterTesting = (): UseParameterTestingReturn => {
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [executionId, setExecutionId] = useState<string | null>(null);
  
  // Refs for polling management
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const pollingAttemptsRef = useRef(0);
  const isCancelledRef = useRef(false);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  // Poll for async execution status
  const pollStatus = useCallback(async (execId: string) => {
    try {
      const status = await maCrossApi.getStatus(execId);
      
      // Check if cancelled
      if (isCancelledRef.current) {
        setIsAnalyzing(false);
        setProgress(0);
        return;
      }

      // Update progress
      setProgress(status.progress || 0);

      // Handle different status states
      switch (status.status) {
        case 'completed':
          // Analysis completed successfully
          if (status.result) {
            const analysisResults = maCrossApi.responseToResults(status.result);
            setResults(analysisResults);
            setError(null);
          }
          setIsAnalyzing(false);
          setProgress(100);
          
          // Clear polling
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          break;

        case 'failed':
          // Analysis failed
          setError(status.error || 'Analysis failed');
          setIsAnalyzing(false);
          setProgress(0);
          
          // Clear polling
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          break;

        case 'running':
        case 'pending':
          // Still processing - continue polling
          pollingAttemptsRef.current++;
          
          // Check max attempts
          if (pollingAttemptsRef.current >= MAX_POLLING_ATTEMPTS) {
            setError('Analysis timeout - exceeded maximum wait time');
            setIsAnalyzing(false);
            setProgress(0);
            
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
          }
          break;
      }
    } catch (err) {
      console.error('Error polling status:', err);
      // Don't stop polling on transient errors
      pollingAttemptsRef.current++;
      
      if (pollingAttemptsRef.current >= MAX_POLLING_ATTEMPTS) {
        setError('Failed to get analysis status');
        setIsAnalyzing(false);
        setProgress(0);
        
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    }
  }, []);

  // Main analysis function
  const analyze = useCallback(async (config: AnalysisConfiguration) => {
    try {
      // Reset state
      setIsAnalyzing(true);
      setError(null);
      setProgress(0);
      setResults([]);
      setExecutionId(null);
      isCancelledRef.current = false;
      pollingAttemptsRef.current = 0;

      // Clear any existing polling
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }

      // Make API call
      const response = await maCrossApi.analyze(config);

      // Handle synchronous response
      if ('portfolios' in response) {
        const syncResponse = response as MACrossSyncResponse;
        
        if (syncResponse.status === 'success') {
          const analysisResults = maCrossApi.responseToResults(syncResponse);
          setResults(analysisResults);
          setProgress(100);
          setIsAnalyzing(false);
        } else {
          throw new Error(syncResponse.error || 'Analysis failed');
        }
      } else {
        // Handle asynchronous response
        const asyncResponse = response as MACrossAsyncResponse;
        setExecutionId(asyncResponse.execution_id);
        
        // Start polling for status
        pollingIntervalRef.current = setInterval(() => {
          pollStatus(asyncResponse.execution_id);
        }, POLLING_INTERVAL);
        
        // Do initial poll immediately
        pollStatus(asyncResponse.execution_id);
      }
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err instanceof Error ? err.message : 'Analysis failed');
      setIsAnalyzing(false);
      setProgress(0);
    }
  }, [pollStatus]);

  // Clear results
  const clearResults = useCallback(() => {
    setResults([]);
    setError(null);
    setProgress(0);
    setExecutionId(null);
  }, []);

  // Cancel ongoing analysis
  const cancelAnalysis = useCallback(() => {
    isCancelledRef.current = true;
    
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    
    setIsAnalyzing(false);
    setProgress(0);
    setExecutionId(null);
  }, []);

  return {
    analyze,
    results,
    isAnalyzing,
    progress,
    error,
    executionId,
    clearResults,
    cancelAnalysis
  };
};
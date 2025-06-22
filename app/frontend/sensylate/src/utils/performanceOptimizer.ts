/**
 * Performance optimization utilities for risk visualization components
 * Includes caching, memoization, and rendering optimizations
 */

import React, { useCallback, useMemo, useRef, useEffect } from 'react';

// Cache configuration
interface CacheConfig {
  ttl: number; // Time to live in milliseconds
  maxSize: number; // Maximum number of cached items
}

interface CacheItem<T> {
  data: T;
  timestamp: number;
  hits: number;
}

/**
 * LRU Cache with TTL support for risk data
 */
export class RiskDataCache<T> {
  private cache = new Map<string, CacheItem<T>>();
  private config: CacheConfig;

  constructor(config: CacheConfig = { ttl: 30000, maxSize: 100 }) {
    this.config = config;
  }

  get(key: string): T | null {
    const item = this.cache.get(key);

    if (!item) return null;

    // Check if item has expired
    if (Date.now() - item.timestamp > this.config.ttl) {
      this.cache.delete(key);
      return null;
    }

    // Update hit count and move to end (LRU)
    item.hits++;
    this.cache.delete(key);
    this.cache.set(key, item);

    return item.data;
  }

  set(key: string, data: T): void {
    // Remove oldest items if cache is full
    if (this.cache.size >= this.config.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      hits: 0,
    });
  }

  clear(): void {
    this.cache.clear();
  }

  size(): number {
    return this.cache.size;
  }

  getStats(): { size: number; hitRate: number; avgAge: number } {
    const items = Array.from(this.cache.values());
    const totalHits = items.reduce((sum, item) => sum + item.hits, 0);
    const totalAccesses = items.length + totalHits;
    const now = Date.now();
    const avgAge =
      items.reduce((sum, item) => sum + (now - item.timestamp), 0) /
      items.length;

    return {
      size: this.cache.size,
      hitRate: totalAccesses > 0 ? totalHits / totalAccesses : 0,
      avgAge: avgAge || 0,
    };
  }
}

// Global cache instances for different data types
export const riskAllocationCache = new RiskDataCache<any>({
  ttl: 30000,
  maxSize: 50,
});
export const chartDataCache = new RiskDataCache<any>({
  ttl: 60000,
  maxSize: 100,
});
export const compositionCache = new RiskDataCache<any>({
  ttl: 45000,
  maxSize: 30,
});

/**
 * Debounced function executor for expensive operations
 */
export function useDebounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T {
  const timeoutRef = useRef<NodeJS.Timeout>();

  return useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        func(...args);
      }, delay);
    },
    [func, delay]
  ) as T;
}

/**
 * Throttled function executor for high-frequency events
 */
export function useThrottle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): T {
  const inThrottle = useRef(false);

  return useCallback(
    (...args: Parameters<T>) => {
      if (!inThrottle.current) {
        func(...args);
        inThrottle.current = true;
        setTimeout(() => {
          inThrottle.current = false;
        }, limit);
      }
    },
    [func, limit]
  ) as T;
}

/**
 * Memoized chart data calculation with caching
 */
export function useMemoizedChartData<T, U>(
  data: T,
  processor: (data: T) => U,
  cacheKey: string,
  dependencies: any[] = []
): U {
  return useMemo(() => {
    // Try to get from cache first
    const cached = chartDataCache.get(cacheKey);
    if (cached) {
      return cached;
    }

    // Process data and cache result
    const result = processor(data);
    chartDataCache.set(cacheKey, result);
    return result;
  }, [data, cacheKey, ...dependencies]);
}

/**
 * Virtualized list rendering for large datasets
 */
export interface VirtualizedListProps {
  items: any[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: any, index: number) => React.ReactNode;
  overscan?: number;
}

export function useVirtualizedList({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 5,
}: VirtualizedListProps) {
  const [scrollTop, setScrollTop] = React.useState(0);

  const visibleRange = useMemo(() => {
    const startIndex = Math.max(
      0,
      Math.floor(scrollTop / itemHeight) - overscan
    );
    const endIndex = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );

    return { startIndex, endIndex };
  }, [scrollTop, itemHeight, containerHeight, items.length, overscan]);

  const visibleItems = useMemo(() => {
    return items
      .slice(visibleRange.startIndex, visibleRange.endIndex + 1)
      .map((item, index) => ({
        item,
        index: visibleRange.startIndex + index,
        offsetY: (visibleRange.startIndex + index) * itemHeight,
      }));
  }, [items, visibleRange, itemHeight]);

  const totalHeight = items.length * itemHeight;

  return {
    visibleItems,
    totalHeight,
    onScroll: (e: React.UIEvent<HTMLDivElement>) => {
      setScrollTop(e.currentTarget.scrollTop);
    },
  };
}

/**
 * Performance monitoring hook
 */
export function usePerformanceMonitor(componentName: string) {
  const renderCount = useRef(0);
  const startTime = useRef(Date.now());

  useEffect(() => {
    renderCount.current++;
    const renderTime = Date.now() - startTime.current;

    if (renderTime > 100) {
      // Log slow renders
      console.warn(
        `[Performance] ${componentName} slow render: ${renderTime}ms (render #${renderCount.current})`
      );
    }

    startTime.current = Date.now();
  });

  return {
    renderCount: renderCount.current,
    logPerformance: (operation: string, duration: number) => {
      if (duration > 50) {
        console.warn(
          `[Performance] ${componentName}.${operation}: ${duration}ms`
        );
      }
    },
  };
}

/**
 * Batch processing for large datasets
 */
export function useBatchProcessor<T, U>(
  items: T[],
  processor: (item: T) => U,
  batchSize: number = 100,
  delay: number = 0
): { results: U[]; isProcessing: boolean; progress: number } {
  const [results, setResults] = React.useState<U[]>([]);
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [progress, setProgress] = React.useState(0);

  useEffect(() => {
    if (items.length === 0) {
      setResults([]);
      setProgress(0);
      return;
    }

    setIsProcessing(true);
    setResults([]);
    setProgress(0);

    const processedResults: U[] = [];
    let currentIndex = 0;

    const processBatch = () => {
      const endIndex = Math.min(currentIndex + batchSize, items.length);

      for (let i = currentIndex; i < endIndex; i++) {
        processedResults.push(processor(items[i]));
      }

      currentIndex = endIndex;
      const newProgress = currentIndex / items.length;

      setResults([...processedResults]);
      setProgress(newProgress);

      if (currentIndex < items.length) {
        if (delay > 0) {
          setTimeout(processBatch, delay);
        } else {
          requestAnimationFrame(processBatch);
        }
      } else {
        setIsProcessing(false);
      }
    };

    processBatch();
  }, [items, processor, batchSize, delay]);

  return { results, isProcessing, progress };
}

/**
 * Smart refresh hook with intelligent scheduling
 */
export function useSmartRefresh(
  refreshFunction: () => void,
  interval: number,
  dependencies: any[] = []
) {
  const isVisible = useRef(true);
  const lastRefresh = useRef(Date.now());
  const intervalRef = useRef<NodeJS.Timeout>();

  // Track page visibility
  useEffect(() => {
    const handleVisibilityChange = () => {
      isVisible.current = !document.hidden;

      if (isVisible.current && Date.now() - lastRefresh.current > interval) {
        refreshFunction();
        lastRefresh.current = Date.now();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () =>
      document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [refreshFunction, interval]);

  // Smart interval management
  useEffect(() => {
    const refresh = () => {
      if (isVisible.current) {
        refreshFunction();
        lastRefresh.current = Date.now();
      }
    };

    intervalRef.current = setInterval(refresh, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [refreshFunction, interval, ...dependencies]);

  return {
    forceRefresh: () => {
      refreshFunction();
      lastRefresh.current = Date.now();
    },
    lastRefreshTime: lastRefresh.current,
  };
}

/**
 * Memory-efficient data transformer
 */
export function useDataTransformer<T, U>(
  data: T[],
  transformer: (item: T) => U,
  options: {
    enableCaching?: boolean;
    cacheKey?: string;
    batchSize?: number;
  } = {}
): { transformedData: U[]; isTransforming: boolean } {
  const { enableCaching = true, cacheKey, batchSize = 1000 } = options;

  const cacheKeyFinal =
    cacheKey || `transform_${JSON.stringify(data).slice(0, 100)}`;

  // Try cache first if enabled
  const cachedResult = enableCaching ? chartDataCache.get(cacheKeyFinal) : null;

  const { results, isProcessing } = useBatchProcessor(
    cachedResult ? [] : data,
    transformer,
    batchSize
  );

  useEffect(() => {
    if (!isProcessing && results.length > 0 && enableCaching) {
      chartDataCache.set(cacheKeyFinal, results);
    }
  }, [isProcessing, results, enableCaching, cacheKeyFinal]);

  return {
    transformedData: cachedResult || results,
    isTransforming: isProcessing,
  };
}

/**
 * Chart rendering optimization hook
 */
export function useChartOptimization(
  width: number,
  height: number,
  dataPoints: number
) {
  // Determine optimal rendering strategy based on data size and viewport
  const shouldUseCanvas = dataPoints > 1000;
  const shouldDecimateData = dataPoints > 5000;
  const optimalPointReduction = shouldDecimateData
    ? Math.floor(dataPoints / 2000)
    : 1;

  // Generate optimal rendering configuration
  const renderConfig = useMemo(
    () => ({
      useCanvas: shouldUseCanvas,
      decimation: optimalPointReduction,
      useWebGL: dataPoints > 10000,
      enableAnimations: dataPoints < 500,
      pointRadius: dataPoints > 1000 ? 0 : dataPoints > 500 ? 1 : 2,
      lineWidth: dataPoints > 2000 ? 1 : 2,
    }),
    [dataPoints, shouldUseCanvas, optimalPointReduction]
  );

  return renderConfig;
}

export default {
  RiskDataCache,
  riskAllocationCache,
  chartDataCache,
  compositionCache,
  useDebounce,
  useThrottle,
  useMemoizedChartData,
  useVirtualizedList,
  usePerformanceMonitor,
  useBatchProcessor,
  useSmartRefresh,
  useDataTransformer,
  useChartOptimization,
};

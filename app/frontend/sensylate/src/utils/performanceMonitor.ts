/**
 * Performance Monitoring and Analytics for Position Sizing System
 * Tracks performance metrics, identifies bottlenecks, and provides optimization insights
 */

import React from 'react';

interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  category: 'render' | 'api' | 'memory' | 'user_interaction';
  component?: string;
  metadata?: Record<string, any>;
}

interface PerformanceThresholds {
  render: {
    component: number; // Component render time threshold (ms)
    chart: number; // Chart rendering threshold (ms)
    interaction: number; // User interaction response threshold (ms)
  };
  api: {
    request: number; // API request threshold (ms)
    cache_hit: number; // Cache hit time threshold (ms)
  };
  memory: {
    heap_size: number; // Max heap size threshold (MB)
    growth_rate: number; // Memory growth rate threshold (MB/min)
  };
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private thresholds: PerformanceThresholds;
  private isProduction: boolean;
  private reportingEndpoint?: string;

  constructor(options: {
    thresholds?: Partial<PerformanceThresholds>;
    isProduction?: boolean;
    reportingEndpoint?: string;
  } = {}) {
    this.thresholds = {
      render: {
        component: 50,
        chart: 200,
        interaction: 100,
        ...options.thresholds?.render
      },
      api: {
        request: 1000,
        cache_hit: 10,
        ...options.thresholds?.api
      },
      memory: {
        heap_size: 100,
        growth_rate: 10,
        ...options.thresholds?.memory
      }
    };

    this.isProduction = options.isProduction ?? process.env.NODE_ENV === 'production';
    this.reportingEndpoint = options.reportingEndpoint;

    this.initializeMonitoring();
  }

  private initializeMonitoring() {
    // Monitor long tasks
    if ('PerformanceObserver' in window) {
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordMetric({
              name: 'long_task',
              value: entry.duration,
              timestamp: entry.startTime,
              category: 'render',
              metadata: { type: entry.entryType }
            });
          }
        });
        longTaskObserver.observe({ entryTypes: ['longtask'] });
      } catch (e) {
        console.warn('Long task monitoring not supported');
      }
    }

    // Monitor memory usage periodically
    this.startMemoryMonitoring();

    // Monitor user interactions
    this.startUserInteractionMonitoring();
  }

  private startMemoryMonitoring() {
    const checkMemory = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        this.recordMetric({
          name: 'memory_usage',
          value: memory.usedJSHeapSize / 1024 / 1024, // Convert to MB
          timestamp: Date.now(),
          category: 'memory',
          metadata: {
            totalHeapSize: memory.totalJSHeapSize / 1024 / 1024,
            heapSizeLimit: memory.jsHeapSizeLimit / 1024 / 1024
          }
        });
      }
    };

    checkMemory();
    setInterval(checkMemory, 30000); // Check every 30 seconds
  }

  private startUserInteractionMonitoring() {
    const measureInteraction = (eventType: string) => (event: Event) => {
      const startTime = Date.now();

      // Use requestAnimationFrame to measure to next frame
      requestAnimationFrame(() => {
        const duration = Date.now() - startTime;
        this.recordMetric({
          name: 'user_interaction',
          value: duration,
          timestamp: startTime,
          category: 'user_interaction',
          metadata: {
            eventType,
            target: (event.target as Element)?.tagName?.toLowerCase()
          }
        });
      });
    };

    document.addEventListener('click', measureInteraction('click'));
    document.addEventListener('input', measureInteraction('input'));
  }

  /**
   * Record a performance metric
   */
  recordMetric(metric: Omit<PerformanceMetric, 'timestamp'> & { timestamp?: number }) {
    const fullMetric: PerformanceMetric = {
      ...metric,
      timestamp: metric.timestamp ?? Date.now()
    };

    this.metrics.push(fullMetric);

    // Keep only last 1000 metrics to prevent memory bloat
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-1000);
    }

    this.checkThresholds(fullMetric);

    if (!this.isProduction) {
      this.logMetric(fullMetric);
    }
  }

  private checkThresholds(metric: PerformanceMetric) {
    let threshold: number | undefined;

    switch (metric.category) {
      case 'render':
        if (metric.name.includes('chart')) {
          threshold = this.thresholds.render.chart;
        } else if (metric.name.includes('interaction')) {
          threshold = this.thresholds.render.interaction;
        } else {
          threshold = this.thresholds.render.component;
        }
        break;
      case 'api':
        threshold = metric.name.includes('cache')
          ? this.thresholds.api.cache_hit
          : this.thresholds.api.request;
        break;
      case 'memory':
        threshold = this.thresholds.memory.heap_size;
        break;
    }

    if (threshold && metric.value > threshold) {
      this.reportPerformanceIssue(metric, threshold);
    }
  }

  private logMetric(metric: PerformanceMetric) {
    const color = this.getLogColor(metric.category);
    console.log(
      `%c[Performance] ${metric.name}: ${metric.value.toFixed(2)}ms`,
      `color: ${color}`,
      metric.component ? `(${metric.component})` : '',
      metric.metadata
    );
  }

  private getLogColor(category: string): string {
    switch (category) {
      case 'render': return '#3b82f6';
      case 'api': return '#10b981';
      case 'memory': return '#f59e0b';
      case 'user_interaction': return '#8b5cf6';
      default: return '#6b7280';
    }
  }

  private reportPerformanceIssue(metric: PerformanceMetric, threshold: number) {
    const issue = {
      type: 'performance_threshold_exceeded',
      metric: metric.name,
      value: metric.value,
      threshold,
      category: metric.category,
      component: metric.component,
      timestamp: metric.timestamp,
      metadata: metric.metadata
    };

    if (!this.isProduction) {
      console.warn('[Performance Issue]', issue);
    }

    if (this.reportingEndpoint) {
      this.sendToReporting(issue);
    }
  }

  private async sendToReporting(data: any) {
    try {
      await fetch(this.reportingEndpoint!, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    } catch (error) {
      console.warn('Failed to send performance data:', error);
    }
  }

  /**
   * Time a function execution
   */
  time<T>(name: string, fn: () => T, component?: string): T {
    const startTime = performance.now();
    const result = fn();
    const duration = performance.now() - startTime;

    this.recordMetric({
      name,
      value: duration,
      category: 'render',
      component
    });

    return result;
  }

  /**
   * Time an async function execution
   */
  async timeAsync<T>(name: string, fn: () => Promise<T>, component?: string): Promise<T> {
    const startTime = performance.now();
    const result = await fn();
    const duration = performance.now() - startTime;

    this.recordMetric({
      name,
      value: duration,
      category: name.includes('api') ? 'api' : 'render',
      component
    });

    return result;
  }

  /**
   * Get performance analytics
   */
  getAnalytics(timeWindow: number = 300000): {
    averages: Record<string, number>;
    maximums: Record<string, number>;
    issueCount: number;
    memoryTrend: { value: number; timestamp: number }[];
    slowestOperations: PerformanceMetric[];
  } {
    const cutoff = Date.now() - timeWindow;
    const recentMetrics = this.metrics.filter(m => m.timestamp > cutoff);

    const grouped = recentMetrics.reduce((acc, metric) => {
      if (!acc[metric.name]) acc[metric.name] = [];
      acc[metric.name].push(metric.value);
      return acc;
    }, {} as Record<string, number[]>);

    const averages = Object.entries(grouped).reduce((acc, [name, values]) => {
      acc[name] = values.reduce((sum, val) => sum + val, 0) / values.length;
      return acc;
    }, {} as Record<string, number>);

    const maximums = Object.entries(grouped).reduce((acc, [name, values]) => {
      acc[name] = Math.max(...values);
      return acc;
    }, {} as Record<string, number>);

    const memoryMetrics = recentMetrics
      .filter(m => m.name === 'memory_usage')
      .map(m => ({ value: m.value, timestamp: m.timestamp }));

    const slowestOperations = recentMetrics
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);

    const issueCount = recentMetrics.filter(m => {
      let threshold: number;
      switch (m.category) {
        case 'render': threshold = this.thresholds.render.component; break;
        case 'api': threshold = this.thresholds.api.request; break;
        case 'memory': threshold = this.thresholds.memory.heap_size; break;
        default: threshold = Infinity;
      }
      return m.value > threshold;
    }).length;

    return {
      averages,
      maximums,
      issueCount,
      memoryTrend: memoryMetrics,
      slowestOperations
    };
  }

  /**
   * Generate performance report
   */
  generateReport(): string {
    const analytics = this.getAnalytics();

    return `
Position Sizing Performance Report
Generated: ${new Date().toISOString()}

PERFORMANCE SUMMARY:
- Total Metrics Recorded: ${this.metrics.length}
- Performance Issues: ${analytics.issueCount}
- Monitoring Window: 5 minutes

RENDER PERFORMANCE:
${Object.entries(analytics.averages)
  .filter(([name]) => name.includes('render') || name.includes('chart'))
  .map(([name, avg]) => `- ${name}: ${avg.toFixed(2)}ms avg, ${analytics.maximums[name]?.toFixed(2)}ms max`)
  .join('\n')}

API PERFORMANCE:
${Object.entries(analytics.averages)
  .filter(([name]) => name.includes('api') || name.includes('request'))
  .map(([name, avg]) => `- ${name}: ${avg.toFixed(2)}ms avg, ${analytics.maximums[name]?.toFixed(2)}ms max`)
  .join('\n')}

MEMORY USAGE:
- Current: ${analytics.memoryTrend[analytics.memoryTrend.length - 1]?.value?.toFixed(2) || 'N/A'}MB
- Trend: ${analytics.memoryTrend.length > 1 ?
    (analytics.memoryTrend[analytics.memoryTrend.length - 1].value - analytics.memoryTrend[0].value > 0 ? 'Increasing' : 'Stable') : 'Insufficient data'}

SLOWEST OPERATIONS:
${analytics.slowestOperations.slice(0, 5)
  .map(op => `- ${op.name}: ${op.value.toFixed(2)}ms ${op.component ? `(${op.component})` : ''}`)
  .join('\n')}

THRESHOLDS:
- Component Render: ${this.thresholds.render.component}ms
- Chart Render: ${this.thresholds.render.chart}ms
- API Request: ${this.thresholds.api.request}ms
- Memory Usage: ${this.thresholds.memory.heap_size}MB
    `.trim();
  }

  /**
   * Clear all recorded metrics
   */
  clear() {
    this.metrics = [];
  }
}

// React hook for performance monitoring
export function usePerformanceMonitor(componentName: string) {
  const monitor = React.useRef<PerformanceMonitor>();

  if (!monitor.current) {
    monitor.current = new PerformanceMonitor();
  }

  const recordRender = React.useCallback((renderTime: number) => {
    monitor.current?.recordMetric({
      name: 'component_render',
      value: renderTime,
      category: 'render',
      component: componentName
    });
  }, [componentName]);

  const timeOperation = React.useCallback(<T,>(name: string, fn: () => T): T => {
    return monitor.current?.time(name, fn, componentName) ?? fn();
  }, [componentName]);

  const timeAsyncOperation = React.useCallback(async <T,>(name: string, fn: () => Promise<T>): Promise<T> => {
    return monitor.current?.timeAsync(name, fn, componentName) ?? fn();
  }, [componentName]);

  return {
    recordRender,
    timeOperation,
    timeAsyncOperation,
    getAnalytics: () => monitor.current?.getAnalytics(),
    generateReport: () => monitor.current?.generateReport()
  };
}

// HOC for automatic component performance monitoring
export function withPerformanceMonitoring<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  componentName?: string
) {
  const PerformanceMonitoredComponent = React.forwardRef<any, P>((props, ref) => {
    const { recordRender } = usePerformanceMonitor(componentName || WrappedComponent.name);
    const renderStartTime = React.useRef<number>();

    React.useLayoutEffect(() => {
      renderStartTime.current = performance.now();
    });

    React.useLayoutEffect(() => {
      if (renderStartTime.current) {
        const renderTime = performance.now() - renderStartTime.current;
        recordRender(renderTime);
      }
    });

    return React.createElement(WrappedComponent, { ...props, ref });
  });

  PerformanceMonitoredComponent.displayName =
    `withPerformanceMonitoring(${componentName || WrappedComponent.name})`;

  return PerformanceMonitoredComponent;
}

// Global performance monitor instance
export const globalPerformanceMonitor = new PerformanceMonitor({
  isProduction: process.env.NODE_ENV === 'production',
  reportingEndpoint: process.env.REACT_APP_PERFORMANCE_ENDPOINT
});

export default PerformanceMonitor;

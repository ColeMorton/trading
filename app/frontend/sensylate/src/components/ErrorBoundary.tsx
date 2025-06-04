import React, { Component, ReactNode } from 'react';
import Icon from './Icon';
import { icons } from '../utils/icons';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Call the optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="container-fluid mt-4">
          <div className="row justify-content-center">
            <div className="col-md-8 col-lg-6">
              <div className="card border-danger">
                <div className="card-header bg-danger text-white">
                  <div className="d-flex align-items-center">
                    <Icon icon={icons.warning} className="me-2" />
                    <h5 className="card-title mb-0">Something went wrong</h5>
                  </div>
                </div>
                <div className="card-body">
                  <p className="card-text">
                    An unexpected error occurred while rendering this component.
                    This could be due to a network issue, invalid data, or a
                    temporary problem.
                  </p>

                  {process.env.NODE_ENV === 'development' &&
                    this.state.error && (
                      <div className="mt-3">
                        <details className="border rounded p-2 bg-light">
                          <summary className="fw-bold text-danger cursor-pointer">
                            Error Details (Development Mode)
                          </summary>
                          <div className="mt-2">
                            <p className="mb-1">
                              <strong>Error:</strong> {this.state.error.message}
                            </p>
                            <p className="mb-1">
                              <strong>Stack:</strong>
                            </p>
                            <pre
                              className="bg-dark text-light p-2 rounded small overflow-auto"
                              style={{ maxHeight: '200px' }}
                            >
                              {this.state.error.stack}
                            </pre>
                            {this.state.errorInfo && (
                              <>
                                <p className="mb-1">
                                  <strong>Component Stack:</strong>
                                </p>
                                <pre
                                  className="bg-dark text-light p-2 rounded small overflow-auto"
                                  style={{ maxHeight: '200px' }}
                                >
                                  {this.state.errorInfo.componentStack}
                                </pre>
                              </>
                            )}
                          </div>
                        </details>
                      </div>
                    )}

                  <div className="mt-3 d-flex gap-2">
                    <button
                      className="btn btn-primary"
                      onClick={this.handleReset}
                    >
                      <Icon icon={icons.refresh} className="me-1" />
                      Try Again
                    </button>
                    <button
                      className="btn btn-outline-secondary"
                      onClick={this.handleReload}
                    >
                      <Icon icon={icons.refresh} className="me-1" />
                      Reload Page
                    </button>
                  </div>

                  <div className="mt-3">
                    <small className="text-muted">
                      If this problem persists, try refreshing the page or
                      clearing your browser cache.
                    </small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

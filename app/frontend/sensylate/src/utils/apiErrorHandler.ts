/**
 * Enhanced error handling utilities for Position Sizing API operations
 * Provides consistent error handling, retry logic, and user-friendly messages
 */

import { AxiosError } from 'axios';

export interface APIError {
  code: string;
  message: string;
  userMessage: string;
  retryable: boolean;
  statusCode?: number;
  context?: Record<string, unknown>;
}

export interface RetryOptions {
  maxRetries: number;
  retryDelay: number;
  backoffMultiplier: number;
  retryableErrors: string[];
}

/**
 * Default retry configuration for Position Sizing operations
 */
export const DEFAULT_RETRY_OPTIONS: RetryOptions = {
  maxRetries: 3,
  retryDelay: 1000, // 1 second
  backoffMultiplier: 2,
  retryableErrors: ['NETWORK_ERROR', 'TIMEOUT', 'SERVER_ERROR', 'RATE_LIMITED'],
};

/**
 * Error codes and their user-friendly messages
 */
const ERROR_MESSAGES: Record<string, { message: string; retryable: boolean }> =
  {
    // Network errors
    NETWORK_ERROR: {
      message:
        'Network connection failed. Please check your internet connection.',
      retryable: true,
    },
    TIMEOUT: {
      message: 'Request timed out. Please try again.',
      retryable: true,
    },

    // Authentication/Authorization
    UNAUTHORIZED: {
      message: 'You are not authorized to perform this action.',
      retryable: false,
    },
    FORBIDDEN: {
      message: 'Access denied. Please check your permissions.',
      retryable: false,
    },

    // Validation errors
    INVALID_INPUT: {
      message: 'Invalid input provided. Please check your data and try again.',
      retryable: false,
    },
    VALIDATION_ERROR: {
      message: 'Data validation failed. Please review the required fields.',
      retryable: false,
    },
    INVALID_POSITION_SIZE: {
      message: 'Position size must be a positive number.',
      retryable: false,
    },
    INVALID_DATE: {
      message: 'Please provide a valid date in YYYY-MM-DD format.',
      retryable: false,
    },
    DUPLICATE_POSITION: {
      message: 'A position for this symbol already exists.',
      retryable: false,
    },

    // Business logic errors
    INSUFFICIENT_FUNDS: {
      message: 'Insufficient funds for this position size.',
      retryable: false,
    },
    RISK_LIMIT_EXCEEDED: {
      message: 'This position would exceed your risk limit (11.8% CVaR).',
      retryable: false,
    },
    PORTFOLIO_FULL: {
      message: 'Portfolio has reached maximum position limit.',
      retryable: false,
    },
    INVALID_TRANSITION: {
      message: 'Cannot transition position in current state.',
      retryable: false,
    },

    // File operations
    CSV_PARSE_ERROR: {
      message: 'Failed to parse CSV file. Please check the format.',
      retryable: false,
    },
    CSV_WRITE_ERROR: {
      message: 'Failed to save CSV file. Please try again.',
      retryable: true,
    },
    FILE_NOT_FOUND: {
      message: 'Requested file not found.',
      retryable: false,
    },
    BACKUP_FAILED: {
      message: 'Failed to create backup before update.',
      retryable: true,
    },

    // Server errors
    SERVER_ERROR: {
      message: 'Server error occurred. Please try again later.',
      retryable: true,
    },
    SERVICE_UNAVAILABLE: {
      message: 'Position sizing service is temporarily unavailable.',
      retryable: true,
    },
    RATE_LIMITED: {
      message: 'Too many requests. Please wait before trying again.',
      retryable: true,
    },

    // Kelly Criterion specific
    KELLY_UPDATE_FAILED: {
      message: 'Failed to update Kelly Criterion value.',
      retryable: true,
    },
    INVALID_KELLY_VALUE: {
      message: 'Kelly Criterion must be between 0 and 1.',
      retryable: false,
    },

    // Generic fallback
    UNKNOWN_ERROR: {
      message: 'An unexpected error occurred. Please try again.',
      retryable: true,
    },
  };

/**
 * Parse error from API response or exception
 */
export function parseAPIError(
  error: unknown,
  context?: Record<string, unknown>
): APIError {
  // Handle Axios errors
  if (error instanceof AxiosError) {
    const statusCode = error.response?.status;
    const responseData = error.response?.data;

    // Extract error code from response
    let errorCode = 'UNKNOWN_ERROR';
    let errorMessage = 'An unexpected error occurred';

    if (responseData?.error?.code) {
      errorCode = responseData.error.code;
    } else if (responseData?.message) {
      errorMessage = responseData.message;
    } else if (error.code === 'ECONNABORTED') {
      errorCode = 'TIMEOUT';
    } else if (error.code === 'ERR_NETWORK') {
      errorCode = 'NETWORK_ERROR';
    } else if (statusCode) {
      switch (statusCode) {
        case 400:
          errorCode = 'VALIDATION_ERROR';
          break;
        case 401:
          errorCode = 'UNAUTHORIZED';
          break;
        case 403:
          errorCode = 'FORBIDDEN';
          break;
        case 404:
          errorCode = 'FILE_NOT_FOUND';
          break;
        case 409:
          errorCode = 'DUPLICATE_POSITION';
          break;
        case 422:
          errorCode = 'INVALID_INPUT';
          break;
        case 429:
          errorCode = 'RATE_LIMITED';
          break;
        case 500:
        case 502:
        case 503:
          errorCode = 'SERVER_ERROR';
          break;
        default:
          errorCode = 'UNKNOWN_ERROR';
      }
    }

    const errorInfo = ERROR_MESSAGES[errorCode] || ERROR_MESSAGES.UNKNOWN_ERROR;

    return {
      code: errorCode,
      message: responseData?.message || error.message || errorMessage,
      userMessage: errorInfo.message,
      retryable: errorInfo.retryable,
      statusCode,
      context,
    };
  }

  // Handle standard errors
  if (error instanceof Error) {
    const errorCode = 'UNKNOWN_ERROR';
    const errorInfo = ERROR_MESSAGES[errorCode];

    return {
      code: errorCode,
      message: error.message,
      userMessage: errorInfo.message,
      retryable: errorInfo.retryable,
      context,
    };
  }

  // Handle unknown error types
  const errorCode = 'UNKNOWN_ERROR';
  const errorInfo = ERROR_MESSAGES[errorCode];

  return {
    code: errorCode,
    message: String(error),
    userMessage: errorInfo.message,
    retryable: errorInfo.retryable,
    context,
  };
}

/**
 * Sleep utility for retry delays
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Retry wrapper for API operations
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  options: Partial<RetryOptions> = {},
  context?: Record<string, unknown>
): Promise<T> {
  const config = { ...DEFAULT_RETRY_OPTIONS, ...options };
  let lastError: APIError;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = parseAPIError(error, context);

      // Don't retry if error is not retryable
      if (!lastError.retryable) {
        throw lastError;
      }

      // Don't retry on final attempt
      if (attempt === config.maxRetries) {
        throw lastError;
      }

      // Calculate delay with exponential backoff
      const delay =
        config.retryDelay * Math.pow(config.backoffMultiplier, attempt);
      console.warn(
        `API operation failed (attempt ${attempt + 1}/${
          config.maxRetries + 1
        }): ${lastError.message}. Retrying in ${delay}ms...`
      );

      await sleep(delay);
    }
  }

  // Should never reach here, but TypeScript needs it
  throw lastError!;
}

/**
 * Validate position data before API calls
 */
export function validatePositionData(position: {
  symbol?: string;
  manualPositionSize?: number;
  manualEntryDate?: string;
  currentStatus?: string;
  stopStatus?: string;
}): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Validate symbol
  if (position.symbol) {
    if (!/^[A-Z0-9-]+$/.test(position.symbol)) {
      errors.push(
        'Symbol must contain only uppercase letters, numbers, and hyphens'
      );
    }
  }

  // Validate position size
  if (position.manualPositionSize !== undefined) {
    if (position.manualPositionSize <= 0) {
      errors.push('Position size must be greater than 0');
    }
    if (position.manualPositionSize > 1000000) {
      errors.push('Position size cannot exceed $1,000,000');
    }
  }

  // Validate entry date
  if (position.manualEntryDate) {
    const date = new Date(position.manualEntryDate);
    if (isNaN(date.getTime())) {
      errors.push('Entry date must be in valid YYYY-MM-DD format');
    } else if (date > new Date()) {
      errors.push('Entry date cannot be in the future');
    }
  }

  // Validate status values
  if (
    position.currentStatus &&
    !['Active', 'Closed', 'Pending'].includes(position.currentStatus)
  ) {
    errors.push('Current status must be Active, Closed, or Pending');
  }

  if (
    position.stopStatus &&
    !['Risk', 'Protected'].includes(position.stopStatus)
  ) {
    errors.push('Stop status must be Risk or Protected');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Validate Kelly Criterion input
 */
export function validateKellyInput(kelly: {
  kellyCriterion?: number;
  source?: string;
}): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (kelly.kellyCriterion !== undefined) {
    if (kelly.kellyCriterion < 0 || kelly.kellyCriterion > 1) {
      errors.push('Kelly Criterion must be between 0 and 1');
    }
  }

  if (
    kelly.source &&
    !['Trading Journal', 'Manual', 'Calculated'].includes(kelly.source)
  ) {
    errors.push('Source must be Trading Journal, Manual, or Calculated');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Create user-friendly error notification
 */
export function createErrorNotification(error: APIError): {
  title: string;
  message: string;
  type: 'error' | 'warning';
  actions?: Array<{ label: string; action: string }>;
} {
  const isRetryable = error.retryable;

  return {
    title: isRetryable ? 'Temporary Error' : 'Error',
    message: error.userMessage,
    type: isRetryable ? 'warning' : 'error',
    actions: isRetryable
      ? [
          { label: 'Retry', action: 'retry' },
          { label: 'Cancel', action: 'cancel' },
        ]
      : [{ label: 'OK', action: 'dismiss' }],
  };
}

export default {
  parseAPIError,
  withRetry,
  validatePositionData,
  validateKellyInput,
  createErrorNotification,
  DEFAULT_RETRY_OPTIONS,
};

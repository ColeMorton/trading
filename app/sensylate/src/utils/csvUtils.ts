/**
 * Converts structured data to raw CSV text format
 * 
 * @param data Array of data objects
 * @param columns Array of column names
 * @returns CSV formatted string
 */
export const convertToRawText = (data: Record<string, any>[], columns: string[]): string => {
  // Create header row
  let rawText = columns.join(',') + '\n';
  
  // Add data rows
  data.forEach(row => {
    const rowValues = columns.map(col => {
      // Get the value and handle null/undefined
      let value = row[col];
      
      // Format numbers appropriately for CSV
      if (typeof value === 'number') {
        // Don't round numbers in the raw CSV data
        value = String(value);
      } else {
        // Handle null/undefined
        value = value !== null && value !== undefined ? String(value) : '';
      }
      
      // Handle values with commas by quoting them
      return value.includes(',') ? `"${value}"` : value;
    });
    rawText += rowValues.join(',') + '\n';
  });
  
  return rawText;
};

/**
 * Creates a clean version of column names by removing special characters
 * 
 * @param columns Array of original column names
 * @returns Object mapping clean keys to original keys
 */
export const createColumnMapping = (columns: string[]): Record<string, string> => {
  const mapping: Record<string, string> = {};
  
  columns.forEach(key => {
    const cleanKey = key.replace(/[\[\]%]/g, '_');
    mapping[cleanKey] = key;
  });
  
  return mapping;
};

/**
 * Creates a clean version of data by replacing special characters in keys
 * 
 * @param data Original data array
 * @returns Cleaned data array
 */
export const cleanData = (data: Record<string, any>[]): Record<string, any>[] => {
  return data.map(row => {
    const cleanRow: Record<string, any> = {};
    Object.keys(row).forEach(key => {
      const cleanKey = key.replace(/[\[\]%]/g, '_');
      cleanRow[cleanKey] = row[key];
    });
    return cleanRow;
  });
};

/**
 * Formats a value for display in the table
 * 
 * @param value The value to format
 * @param columnName The original column name
 * @returns Formatted value as string
 */
export const formatValue = (value: any, columnName: string): string => {
  // Handle null/undefined values
  if (value === null || value === undefined) {
    return '';
  }
  
  // Special handling for percentage columns
  if (
    columnName.includes('[%]') ||
    columnName.toLowerCase().includes('rate') ||
    columnName.toLowerCase().includes('percent')
  ) {
    if (typeof value === 'number') {
      return `${value.toFixed(2)}%`;
    } else if (typeof value === 'string' && !isNaN(parseFloat(value))) {
      return `${parseFloat(value).toFixed(2)}%`;
    }
  }
  
  // Format numbers with appropriate precision
  if (typeof value === 'number') {
    if (value === 0) {
      return '0';
    } else if (Math.abs(value) < 0.01) {
      return value.toExponential(4);
    } else if (Math.abs(value) >= 1000) {
      return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
    } else {
      return value.toLocaleString(undefined, { maximumFractionDigits: 4 });
    }
  }
  
  return String(value);
};
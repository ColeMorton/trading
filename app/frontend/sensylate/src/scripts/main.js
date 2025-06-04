// CSS is now imported via React in index.css

document.addEventListener('DOMContentLoaded', function () {
  const fileSelector = document.getElementById('file-selector');
  const tableContainer = document.getElementById('table-container');
  const textContainer = document.getElementById('text-container');
  const loadingIndicator = document.getElementById('loading');
  const errorMessage = document.getElementById('error-message');
  const fileInfo = document.getElementById('file-info');
  const tableViewBtn = document.getElementById('table-view-btn');
  const textViewBtn = document.getElementById('text-view-btn');
  const csvText = document.getElementById('csv-text');

  // Function to switch to table view
  function showTableView() {
    tableContainer.classList.remove('hidden');
    textContainer.classList.add('hidden');
    tableViewBtn.classList.remove('bg-gray-200', 'text-gray-700');
    tableViewBtn.classList.add('bg-indigo-600', 'text-white');
    textViewBtn.classList.remove('bg-indigo-600', 'text-white');
    textViewBtn.classList.add('bg-gray-200', 'text-gray-700');
  }

  // Function to switch to text view
  function showTextView() {
    tableContainer.classList.add('hidden');
    textContainer.classList.remove('hidden');
    tableViewBtn.classList.remove('bg-indigo-600', 'text-white');
    tableViewBtn.classList.add('bg-gray-200', 'text-gray-700');
    textViewBtn.classList.remove('bg-gray-200', 'text-gray-700');
    textViewBtn.classList.add('bg-indigo-600', 'text-white');
  }

  // Event listeners for toggle buttons
  tableViewBtn.addEventListener('click', showTableView);
  textViewBtn.addEventListener('click', showTextView);

  // Function to convert CSV data to raw text
  function convertToRawText(data, columns) {
    // Create header row
    let rawText = columns.join(',') + '\n';

    // Add data rows
    data.forEach((row) => {
      const rowValues = columns.map((col) => {
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
  }

  // Function to show error
  function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
    loadingIndicator.classList.add('hidden');
  }

  // Function to load file list
  function loadFileList() {
    loadingIndicator.classList.remove('hidden');

    fetch('/api/data/list/strategies')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Failed to load file list');
        }
        return response.json();
      })
      .then((data) => {
        loadingIndicator.classList.add('hidden');

        if (!data || !data.files) {
          throw new Error('Invalid response format');
        }

        // Filter for CSV files only
        const csvFiles = data.files.filter((file) =>
          file.path.endsWith('.csv')
        );

        // Sort files by filename (not the full path)
        csvFiles.sort((a, b) => {
          const filenameA = a.path.split('/').pop();
          const filenameB = b.path.split('/').pop();
          return filenameA.localeCompare(filenameB);
        });

        // Add sorted files to selector
        csvFiles.forEach((file) => {
          const option = document.createElement('option');
          option.value = file.path;
          option.textContent = file.path.split('/').pop();
          fileSelector.appendChild(option);
        });

        // Check if DAILY.csv exists in the list and select it by default
        const dailyOption = Array.from(fileSelector.options).find(
          (option) => option.textContent === 'DAILY.csv'
        );

        if (dailyOption) {
          fileSelector.value = dailyOption.value;
          // Trigger change event to load the file
          const changeEvent = new Event('change');
          fileSelector.dispatchEvent(changeEvent);
        }
      })
      .catch((error) => {
        showError('Error loading file list: ' + error.message);
      });
  }

  // Function to load CSV data
  function loadCSVData(filePath) {
    loadingIndicator.classList.remove('hidden');
    tableContainer.classList.add('hidden');
    textContainer.classList.add('hidden');
    errorMessage.classList.add('hidden');
    document.getElementById('view-toggle').classList.add('hidden');

    fetch(`/api/data/csv/${filePath}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error('Failed to load CSV file');
        }
        return response.json();
      })
      .then((response) => {
        // Hide loading indicator
        loadingIndicator.classList.add('hidden');

        if (!response || !response.data || !response.data.data) {
          showError('Invalid response format');
          return;
        }

        const data = response.data.data;

        if (data.length === 0) {
          showError('No data found in the CSV file.');
          return;
        }

        // Debug: Check for Win Rate [%] column and its values
        console.log('All columns:', Object.keys(data[0]));
        const winRateKey = Object.keys(data[0]).find(
          (key) => key.includes('Win Rate') || key.includes('Win_Rate')
        );

        if (winRateKey) {
          console.log(`Found Win Rate column: "${winRateKey}"`);
          console.log(
            'First few Win Rate values:',
            data.slice(0, 5).map((row) => ({
              value: row[winRateKey],
              type: typeof row[winRateKey],
            }))
          );
        } else {
          console.log('No Win Rate column found in data');
        }

        // Display file info
        fileInfo.innerHTML = `
                    <p><strong>File:</strong> ${filePath.split('/').pop()}</p>
                    <p><strong>Rows:</strong> ${data.length}</p>
                    <p><strong>Columns:</strong> ${
                      Object.keys(data[0]).length
                    }</p>
                `;

        // Show view toggle buttons
        document.getElementById('view-toggle').classList.remove('hidden');

        // Get columns
        const columns = Object.keys(data[0]);
        // Populate raw text view with original data (not the cleaned version)
        const rawText = convertToRawText(data, columns);
        csvText.value = rawText;

        // Show table view by default
        showTableView();

        // Find the index of the "Score" column
        const scoreColumnIndex = columns.findIndex((col) => col === 'Score');

        // Log the data to help debug
        console.log('CSV Data Sample:', data.slice(0, 3));

        // Check for Win Rate column
        const winRateColumn = columns.find(
          (col) => col.includes('Win Rate') || col.includes('Win_Rate')
        );
        if (winRateColumn) {
          console.log(`Win Rate column found: "${winRateColumn}"`);
          console.log(
            'Sample Win Rate values:',
            data.slice(0, 3).map((row) => row[winRateColumn])
          );
        } else {
          console.log('No Win Rate column found in:', columns);
        }

        // Create a clean version of the data for DataTables
        // This addresses issues with columns containing special characters like [%]
        const cleanData = data.map((row) => {
          const cleanRow = {};
          Object.keys(row).forEach((key) => {
            // Create a clean key without special characters for internal use
            const cleanKey = key.replace(/[\[\]%]/g, '_');
            cleanRow[cleanKey] = row[key];
          });
          return cleanRow;
        });

        // Create a mapping between original column names and clean column names
        const columnMapping = {};
        columns.forEach((key) => {
          const cleanKey = key.replace(/[\[\]%]/g, '_');
          columnMapping[cleanKey] = key;
        });

        // Log the column mapping for debugging
        console.log('Column mapping:', columnMapping);

        // Get clean column names
        const cleanColumns = Object.keys(cleanData[0]);

        // Initialize DataTable
        $('#csv-table').DataTable({
          destroy: true, // Destroy existing table
          data: cleanData,
          columns: cleanColumns.map((cleanKey) => {
            // Get the original key for display
            const originalKey = columnMapping[cleanKey];

            // Log column data types for debugging
            const sampleValues = cleanData
              .slice(0, 3)
              .map((row) => row[cleanKey]);
            console.log(
              `Column "${originalKey}" (${cleanKey}) sample values:`,
              sampleValues
            );

            return {
              // Use original key with special characters for display
              title: originalKey,
              // Use clean key for data access
              data: cleanKey,
              // Ensure proper rendering of all data types
              render: function (data, type, row) {
                // For sorting and type detection
                if (type === 'sort' || type === 'type') {
                  return data === null || data === undefined ? '' : data;
                }

                // For display
                if (data === null || data === undefined) {
                  return '';
                }

                // Special handling for percentage columns
                if (
                  originalKey.includes('[%]') ||
                  originalKey.toLowerCase().includes('rate') ||
                  originalKey.toLowerCase().includes('percent')
                ) {
                  console.log(
                    `Rendering percentage value: ${data}, type: ${typeof data}`
                  );
                  if (typeof data === 'number') {
                    return data.toFixed(2) + '%';
                  } else if (
                    typeof data === 'string' &&
                    !isNaN(parseFloat(data))
                  ) {
                    return parseFloat(data).toFixed(2) + '%';
                  }
                }

                // Format numbers with appropriate precision
                if (typeof data === 'number') {
                  // Special case for zero
                  if (data === 0) {
                    return '0';
                  }
                  // For score and other decimal values
                  else if (Math.abs(data) < 0.01) {
                    return data.toExponential(4);
                  } else if (Math.abs(data) >= 1000) {
                    return data.toLocaleString(undefined, {
                      maximumFractionDigits: 2,
                    });
                  } else {
                    return data.toLocaleString(undefined, {
                      maximumFractionDigits: 4,
                    });
                  }
                }

                return data;
              },
            };
          }),
          scrollX: true,
          scrollY: '70vh',
          scrollCollapse: true,
          paging: false,
          searching: true,
          ordering: true,
          info: true,
          lengthMenu: [
            [10, 25, 50, 100, -1],
            [10, 25, 50, 100, 'All'],
          ],
          pageLength: 'All',
          responsive: true,
          // Set default sort to "Score" column in descending order if it exists
          order: scoreColumnIndex !== -1 ? [[scoreColumnIndex, 'desc']] : [],
        });
      })
      .catch((error) => {
        showError('Error loading CSV file: ' + error.message);
      });
  }
  // Event listener for file selector
  fileSelector.addEventListener('change', function () {
    if (this.value) {
      loadCSVData(this.value);

      // Enable Update button when a file is selected
      const updateButton = document.getElementById('update-button');
      updateButton.disabled = false;
    } else {
      // Disable Update button when no file is selected
      const updateButton = document.getElementById('update-button');
      updateButton.disabled = true;
    }
  });

  // Add event listener for Update button
  document
    .getElementById('update-button')
    .addEventListener('click', function () {
      const filePath = fileSelector.value;
      if (!filePath) return;

      // Show loading state
      this.disabled = true;
      this.innerHTML =
        '<span class="animate-spin inline-block mr-2">↻</span> Updating...';

      // Hide previous status
      const updateStatus = document.getElementById('update-status');
      updateStatus.classList.add('hidden');

      // Get just the filename without the path
      const fileName = filePath.split('/').pop();

      // Make API request to update portfolio
      fetch('/api/scripts/update-portfolio', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          portfolio: fileName,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          // Show status message
          updateStatus.classList.remove('hidden');

          if (data.status === 'accepted') {
            updateStatus.className =
              'mb-4 p-3 bg-blue-100 text-blue-800 rounded shadow-sm';
            updateStatus.textContent = `Portfolio update started. Execution ID: ${data.execution_id}`;
            // Store button reference for use in event handlers
            const updateButton = this;

            // Create SSE connection
            const executionId = data.execution_id;
            const eventSource = new EventSource(
              `/api/scripts/status-stream/${executionId}`
            );

            // Handle incoming messages
            eventSource.onmessage = function (event) {
              try {
                const statusData = JSON.parse(event.data);

                // Update status message based on progress
                if (statusData.status === 'completed') {
                  // Update status message
                  updateStatus.className =
                    'mb-4 p-3 bg-green-100 text-green-800 rounded shadow-sm';
                  updateStatus.textContent = 'Portfolio updated successfully!';

                  // Reset button
                  updateButton.disabled = false;
                  updateButton.textContent = 'Update';

                  // Reload the CSV data to refresh the table
                  loadCSVData(filePath);

                  // Close the connection
                  eventSource.close();
                } else if (statusData.status === 'failed') {
                  // Update status message
                  updateStatus.className =
                    'mb-4 p-3 bg-red-100 text-red-800 rounded shadow-sm';
                  updateStatus.textContent = `Update failed: ${
                    statusData.error || 'Unknown error'
                  }`;

                  // Reset button
                  updateButton.disabled = false;
                  updateButton.textContent = 'Update';

                  // Close the connection
                  eventSource.close();
                } else {
                  // Update progress message
                  const progressText = statusData.progress
                    ? `(${statusData.progress}%)`
                    : '';
                  updateStatus.textContent = `Portfolio update in progress... Status: ${statusData.status} ${progressText}`;

                  // Add progress bar if not already present
                  if (!document.getElementById('progress-bar-container')) {
                    const progressContainer = document.createElement('div');
                    progressContainer.id = 'progress-bar-container';
                    progressContainer.className =
                      'w-full bg-gray-200 rounded-full h-2.5 mt-2';

                    const progressBar = document.createElement('div');
                    progressBar.id = 'progress-bar';
                    progressBar.className = 'bg-indigo-600 h-2.5 rounded-full';
                    progressBar.style.width = `${statusData.progress || 0}%`;

                    progressContainer.appendChild(progressBar);
                    updateStatus.appendChild(progressContainer);
                  } else {
                    // Update existing progress bar
                    const progressBar = document.getElementById('progress-bar');
                    if (progressBar) {
                      progressBar.style.width = `${statusData.progress || 0}%`;
                    }
                  }
                }
              } catch (error) {
                console.error('Error parsing SSE message:', error);
              }
            };

            // Handle connection errors
            eventSource.onerror = function (error) {
              console.error('SSE connection error:', error);

              // Update status message
              updateStatus.className =
                'mb-4 p-3 bg-red-100 text-red-800 rounded shadow-sm';
              updateStatus.textContent = `Error checking status: Connection lost`;

              // Reset button
              updateButton.disabled = false;
              updateButton.textContent = 'Update';

              // Close the connection
              eventSource.close();
            };
          } else {
            updateStatus.className =
              'mb-4 p-3 bg-red-100 text-red-800 rounded shadow-sm';
            updateStatus.textContent = `Error: ${
              data.message || 'Unknown error'
            }`;

            // Reset button
            this.disabled = false;
            this.textContent = 'Update';
          }
        })
        .catch((error) => {
          // Reset button
          this.disabled = false;
          this.textContent = 'Update';

          // Show error message
          updateStatus.classList.remove('hidden');
          updateStatus.className =
            'mb-4 p-3 bg-red-100 text-red-800 rounded shadow-sm';
          updateStatus.textContent = `Error starting update: ${error.message}`;
        });
    });

  // Load file list on page load
  loadFileList();
});

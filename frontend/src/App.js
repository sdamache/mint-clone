import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function getBackendUrl() {
  // Use environment variable if available
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  // Default to localhost for development
  return 'http://localhost:5001';
}

function App() {
  const [file, setFile] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [stats, setStats] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const transactionsPerPage = 10;

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    console.log('Selected file:', selectedFile);
    
    if (selectedFile && !selectedFile.name.endsWith('.csv')) {
      console.warn('Invalid file type selected');
      setError('Please select a CSV file');
      return;
    }
    setFile(selectedFile);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      console.log('Preparing to upload file:', file.name);
      const backendUrl = getBackendUrl();
      console.log('Using backend URL:', backendUrl);
      
      const response = await axios.post(`${backendUrl}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Accept': 'application/json'
        },
        timeout: 30000,
        validateStatus: false,
        withCredentials: true,
        responseType: 'json',
        onUploadProgress: (progressEvent) => {
          console.log('Upload Progress:', Math.round((progressEvent.loaded * 100) / progressEvent.total));
        }
      });

      // Log the response data
      console.log('Response data:', response.data);

      // Parse response if it's a string
      let responseData;
      try {
        responseData = typeof response.data === 'string' ? JSON.parse(response.data) : response.data;
      } catch (e) {
        console.error('Response parsing error:', {
          error: e,
          responseData: response.data,
          responseType: typeof response.data
        });
        throw new Error(`Invalid response format: Unable to parse response - ${e.message}`);
      }

      // Validate parsed response and ensure numeric values are valid
      const transformedTransactions = responseData.transactions
        .filter(t => t && typeof t === 'object')
        .map(t => {
          let parsedDate;
          try {
            parsedDate = new Date(t.Date).toLocaleDateString();
          } catch (dateError) {
            console.error('Date parsing error:', {
              date: t.Date,
              error: dateError
            });
            parsedDate = 'Invalid Date';
          }
          return {
            ...t,
            date: parsedDate,
            amount: typeof t.Amount === 'number' && !isNaN(t.Amount) ? t.Amount : 0,
            description: String(t.Description || ''),
            category: String(t.Category || 'Miscellaneous')
          };
        })
        .filter(t => t.date !== 'Invalid Date' && t.description);

      if (transformedTransactions.length === 0) {
        throw new Error('No valid transactions found in response');
      }

      // Sort transactions by date in descending order
      transformedTransactions.sort((a, b) => new Date(b.date) - new Date(a.date));

      console.log('Processed transactions:', transformedTransactions);
      
      setTransactions(transformedTransactions);
      setStats(responseData.stats);
      setSuccess(`Successfully uploaded ${transformedTransactions.length} transactions`);

    } catch (error) {
      console.error('Upload error:', {
        message: error.message,
        name: error.name,
        code: error.code,
        stack: error.stack,
        response: error?.response?.data,
        rawResponse: error?.response
      });
      
      let errorMessage;
      if (error.code === 'ECONNREFUSED') {
        errorMessage = 'Cannot connect to server. Please ensure the backend is running.';
      } else if (error.code === 'CORS_ERROR') {
        errorMessage = 'Cross-origin request blocked. Please check CORS settings.';
      } else {
        errorMessage = error.response?.data?.error 
          || error.message 
          || 'Error uploading file. Please try again.';
      }
      
      setError(`Upload failed: ${errorMessage}`);
    } finally {
      setUploading(false);
    }
  };

  // Get current transactions
  const indexOfLastTransaction = currentPage * transactionsPerPage;
  const indexOfFirstTransaction = indexOfLastTransaction - transactionsPerPage;
  const currentTransactions = transactions.slice(indexOfFirstTransaction, indexOfLastTransaction);

  // Change page
  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  const nextPage = () => {
    if (currentPage < Math.ceil(transactions.length / transactionsPerPage)) {
      setCurrentPage(currentPage + 1);
    }
  };

  const prevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1 className="app-name">Personal Finance Tracker</h1>
        
        <div className="upload-section">
          <input 
            type="file" 
            onChange={handleFileChange}
            accept=".csv"
            disabled={uploading}
          />
          <button 
            onClick={handleUpload}
            className={file ? 'green' : ''}
            disabled={!file || uploading}
          >
            {uploading ? 'Uploading...' : 'Upload CSV'}
          </button>
        </div>

        {error && <p className="error">{error}</p>}
        {success && <p className="success">{success}</p>}
        
        {stats && (
          <div className="stats">
            <h3>Upload Summary</h3>
            <table className="summary-table">
              <tbody>
                <tr>
                  <td>Total Transactions:</td>
                  <td>{stats.total_rows}</td>
                </tr>
                <tr>
                  <td>Total Amount:</td>
                  <td>${stats.total_amount.toFixed(2)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {transactions.length > 0 && (
          <div className="transactions">
            <h3>Recent Transactions</h3>
            <table className="centered-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Amount</th>
                  <th>Category</th>
                </tr>
              </thead>
              <tbody>
                {currentTransactions.map((transaction, index) => (
                  <tr key={index}>
                    <td>{transaction.date}</td>
                    <td>{transaction.description}</td>
                    <td>${transaction.amount.toFixed(2)}</td>
                    <td>{transaction.category}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="pagination">
              <button onClick={prevPage} disabled={currentPage === 1}>
                Previous
              </button>
              <span> Page {currentPage} of {Math.ceil(transactions.length / transactionsPerPage)} </span>
              <button onClick={nextPage} disabled={currentPage === Math.ceil(transactions.length / transactionsPerPage)}>
                Next
              </button>
            </div>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;

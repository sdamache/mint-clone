import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [stats, setStats] = useState(null);

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
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000,
        validateStatus: false,
        withCredentials: true,
        onUploadProgress: (progressEvent) => {
          console.log('Upload Progress:', Math.round((progressEvent.loaded * 100) / progressEvent.total));
        }
      });

      console.log('Raw response:', response);

      // Check if the response status is not successful
      if (response.status !== 200) {
        throw new Error(`Server returned ${response.status}: ${JSON.stringify(response.data)}`);
      }

      if (response.data.transactions) {
        // Transform the transaction data to match backend structure
        const transformedTransactions = response.data.transactions.map(t => ({
          ...t,
          // Ensure proper date formatting
          date: new Date(t.date).toLocaleDateString(),
          // Ensure proper number formatting
          amount: parseFloat(t.amount),
        }));

        setTransactions(transformedTransactions);
        setStats(response.data.stats);
        setSuccess(`Successfully uploaded ${response.data.stats.total_rows} transactions`);
      } else {
        throw new Error('No transaction data in response');
      }
    } catch (error) {
      console.error('Upload error:', {
        message: error.message,
        name: error.name,
        code: error.code,
        stack: error.stack,
        response: error.response,
        request: error.request
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

  return (
    <div className="App">
      <header className="App-header">
        <h1>Personal Finance Tracker</h1>
        
        <div className="upload-section">
          <input 
            type="file" 
            onChange={handleFileChange}
            accept=".csv"
            disabled={uploading}
          />
          <button 
            onClick={handleUpload}
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
            <p>Total Transactions: {stats.total_rows}</p>
            <p>Total Amount: ${stats.total_amount.toFixed(2)}</p>
          </div>
        )}

        {transactions.length > 0 && (
          <div className="transactions">
            <h3>Recent Transactions</h3>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Amount</th>
                  <th>Category</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((transaction, index) => (
                  <tr key={index}>
                    <td>{transaction.date}</td>
                    <td>{transaction.description}</td>
                    <td>${transaction.amount.toFixed(2)}</td>
                    <td>{transaction.category}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;

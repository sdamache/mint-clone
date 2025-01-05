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
      console.warn('No file selected');
      setError('Please select a file to upload.');
      return;
    }

    console.log('Starting file upload:', file.name);
    const formData = new FormData();
    formData.append('file', file);
    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      console.log('Sending request to server...');
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      console.log('Upload response:', response.data);
      setTransactions(response.data.transactions);
      setStats(response.data.stats);
      setSuccess(`Successfully uploaded ${response.data.stats.total_rows} transactions`);
    } catch (error) {
      console.error('Upload error:', error);
      console.error('Error response:', error.response?.data);
      setError(error.response?.data?.error || 'Error uploading file. Please try again.');
    } finally {
      setUploading(false);
      console.log('Upload process completed');
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
                    <td>{new Date(transaction.Date).toLocaleDateString()}</td>
                    <td>{transaction.Description}</td>
                    <td>${transaction.Amount.toFixed(2)}</td>
                    <td>{transaction.Category}</td>
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

import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import BudgetDashboard from './components/BudgetDashboard';

function App() {
  const [file, setFile] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:5001/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      console.log('Upload response:', response.data);
      
      if (response.data && response.data.transactions && Array.isArray(response.data.transactions)) {
        setTransactions(response.data.transactions);
        setError(null);
        // Add success message
        alert(`Successfully uploaded ${response.data.rows_processed} transactions!`);
      } else {
        console.error('No transactions were processed:', response.data);
        setError('No transactions were processed.');
      }
    } catch (error) {
      console.error('Upload error:', error.response?.data || error.message);
      setError(error.response?.data?.error || 'Error uploading file. Please try again.');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Personal Finance Tracker</h1>
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload}>Upload CSV</button>
        {error && <p className="error">{error}</p>}
        <div className="transactions">
          {transactions.length > 0 && (
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
                    <td>{transaction.Date}</td>
                    <td>{transaction.Description}</td>
                    <td>{transaction.Amount}</td>
                    <td>{transaction.Category}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <BudgetDashboard />
      </header>
    </div>
  );
}

export default App;

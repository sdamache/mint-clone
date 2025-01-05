import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload.');
      setSuccess(null);
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setTransactions(response.data.transactions);
      setError(null);
      setSuccess('File uploaded successfully.');
    } catch (error) {
      setError('Error uploading file. Please try again.');
      setSuccess(null);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Personal Finance Tracker</h1>
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload}>Upload CSV</button>
        {error && <p className="error">{error}</p>}
        {success && <p className="success">{success}</p>}
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
      </header>
    </div>
  );
}

export default App;

import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Container, Row, Col } from 'react-bootstrap';
import BudgetDashboard from './components/BudgetDashboard';
import UploadCSV from './components/UploadCSV';

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
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setTransactions(response.data.transactions);
      setError(null);
    } catch (error) {
      setError('Error uploading file. Please try again.');
    }
  };

  return (
    <BrowserRouter>
      <Container fluid>
        <Row>
          <Col md={2}>
            {/* Sidebar component will be added here */}
          </Col>
          <Col md={10}>
            <Routes>
              <Route path="/" element={<BudgetDashboard />} />
              <Route path="/upload" element={<UploadCSV />} />
            </Routes>
          </Col>
        </Row>
      </Container>
    </BrowserRouter>
  );
}

export default App;

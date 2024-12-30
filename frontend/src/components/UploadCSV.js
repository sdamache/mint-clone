import React, { useState } from 'react';
import axios from 'axios';
import { Card, Button } from 'react-bootstrap';

function UploadCSV() {
  const [file, setFile] = useState(null);
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
      await axios.post('http://localhost:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setError(null);
    } catch (error) {
      setError('Error uploading file. Please try again.');
    }
  };

  return (
    <Card className="upload-container">
      <Card.Body>
        <input type="file" onChange={handleFileChange} />
        <Button onClick={handleUpload}>Upload CSV</Button>
        {error && <p className="error">{error}</p>}
      </Card.Body>
    </Card>
  );
}

export default UploadCSV;

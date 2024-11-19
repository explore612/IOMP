import React, { useState } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';

function ManageData() {
  const [message, setMessage] = useState('');

  // Function to handle Load Data API call
  const handleLoadData = async () => {
    setMessage('Loading data...');
    try {
      const response = await axios.post('http://localhost:5001/api/load_data');
      setMessage(response.data.message || 'Data loaded successfully.');
    } catch (error) {
      console.error('Error loading data:', error);
      setMessage('Failed to load data.');
    }
  };

  // Function to handle Generate Embeddings API call
  const handleGenerateEmbeddings = async () => {
    setMessage('Generating embeddings...');
    try {
      const response = await axios.post('http://localhost:5001/api/generate_embeddings');
      setMessage(response.data.message || 'Embeddings generated successfully.');
    } catch (error) {
      console.error('Error generating embeddings:', error);
      setMessage('Failed to generate embeddings.');
    }
  };

  return (
    <div className="container mt-5">
      <h2 className="mb-4 text-center">Manage Data</h2>

      {/* Load Data Button in Green */}
      <button
        className="btn btn-success w-100 mb-3"
        onClick={handleLoadData}
      >
        Load Data
      </button>

      {/* Generate Embeddings Button in Green */}
      <button
        className="btn btn-success w-100 mb-3"
        onClick={handleGenerateEmbeddings}
      >
        Generate Embeddings
      </button>

      {/* Status Message */}
      {message && <div className="alert alert-info mt-4">{message}</div>}
    </div>
  );
}

export default ManageData;

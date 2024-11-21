import React, { useState } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';
import { FaSearch } from 'react-icons/fa';
import ReactMarkdown from "react-markdown";

function Home() {
  const [title, setTitle] = useState('');
  const [abstract, setAbstract] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  // Function to handle search request
  const handleSearch = async () => {
    setLoading(true);
    setResults([]);

    try {
      const response = await axios.post('http://localhost:5001/api/find_similar_projects', {
        text: title,
        abstract: abstract,
      });
      setResults(response.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mt-5">
      <h1 className="mb-4 text-center">Project Similarity Search</h1>

      {/* Input for Project Title */}
      <div className="mb-3">
        <input
          type="text"
          className="form-control"
          placeholder="Enter project title..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
      </div>

      {/* Input for Project Abstract */}
      <div className="mb-3">
        <textarea
          className="form-control"
          placeholder="Enter project abstract..."
          value={abstract}
          onChange={(e) => setAbstract(e.target.value)}
          rows={4}
        />
      </div>

      {/* Search Button */}
      <button
        className="btn btn-success w-100 mb-4"
        onClick={handleSearch}
        disabled={loading}
      >
        {loading ? (
          <div className="d-flex align-items-center">
            <div className="spinner-border spinner-border-sm me-2" role="status" />
            Searching...
          </div>
        ) : (
          <>
            <FaSearch className="me-2" />
            Search
          </>
        )}
      </button>

      {/* Results Section */}
      {results.length > 0 ? (
        <div className="mt-4">
          <h2 className="text-center">Top Similar Projects</h2>
          <table className="table table-bordered mt-3">
            <thead>
              <tr>
                <th>Project ID</th>
                <th>Title</th>
                <th>Abstract</th>
                <th>Similarity Score</th>
                <th>Comments</th>
              </tr>
            </thead>
            <tbody>
              {results.map((result) => (
                <tr key={result.id}>
                  <td>{result.id}</td>
                  {/* Justified Title */}
                  <td className="text-justify justified-text">{result.title}</td>
                  {/* Justified Abstract */}
                  <td className="text-justify justified-text">{result.abstract}</td>
                  <td>{JSON.stringify(result.matching_score)}</td>
                  <td> <ReactMarkdown>{result.matching_comments}</ReactMarkdown></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        !loading && (
          <div className="text-center mt-4">
            <p>No similar projects found. Please try a different search.</p>
          </div>
        )
      )}
    </div>
  );
}

export default Home;

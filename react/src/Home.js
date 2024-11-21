import React, { useState } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import { FaSearch, FaThumbsUp, FaThumbsDown, FaMeh } from "react-icons/fa";
import ReactMarkdown from "react-markdown";

function Home() {
  const [title, setTitle] = useState("");
  const [abstract, setAbstract] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [decision, setDecision] = useState(null);

  // Function to handle search request
  const handleSearch = async () => {
    setLoading(true);
    setResults([]);
    setDecision(null);

    try {
      const response = await axios.post(
        "http://localhost:5001/api/find_similar_projects",
        {
          text: title,
          abstract: abstract,
        }
      );
      setResults(response.data);

      // Calculate average matching score and set decision
      if (response.data.length > 0) {
        const maxScore = Math.max(...response.data.map(result => result.matching_score));
        setDecision(getDecision(maxScore));
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  // Function to get decision based on average score
  const getDecision = (maxScore) => {
    if (maxScore >= 85) {
      return {
        message: "Not Recommended: Too Similar",
        icon: <FaThumbsDown className="text-danger" />,
        color: "danger",
      };
    } else if (maxScore >= 50) {
      return {
        message: "Neutral: Review Carefully",
        icon: <FaMeh className="text-warning" />,
        color: "warning",
      };
    } else {
      return {
        message: "Recommended: Good to Go",
        icon: <FaThumbsUp className="text-success" />,
        color: "success",
      };
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

      {/* Decision Bar */}
      {decision && (
        <div
          className={`alert alert-${decision.color} text-center d-flex align-items-center justify-content-center mb-4`}
          role="alert"
        >
          {decision.icon}
          <span className="ms-2">{decision.message}</span>
        </div>
      )}

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
                <th>Matching Score</th>
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
                  <td>
                    {/* Matching Score */}
                    <span className="matching-score">
                      {result.matching_score}%
                    </span>
                  </td>
                  <td>
                    <ReactMarkdown>{result.matching_comments}</ReactMarkdown>
                  </td>
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

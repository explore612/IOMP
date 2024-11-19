import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Home from './Home';
import ManageData from './ManageData';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  return (
    <Router>
      <div className="container mt-5">
        {/* Navigation Bar */}
        <nav className="d-flex justify-content-start mb-4">
          {/* Align Home and Manage Data buttons to the left */}
          <Link to="/" className="btn btn-success me-2">Home</Link>
          <Link to="/manage-data" className="btn btn-success">Manage Data</Link>
        </nav>

        {/* App Routes */}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/manage-data" element={<ManageData />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

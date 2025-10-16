import React, { useState, useEffect } from 'react';
import './App.css';
import { useAuth } from './contexts/AuthContext';
import Login from './components/login';
import Register from './components/register';

const API_BASE_URL = 'http://localhost:8000';

// Utility function for API calls
const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  };
  
  const response = await fetch(url, config);
  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }
  return response.json();
};


// Database Status Component
const DatabaseStatus = ({ status, onRefresh }) => {
  return (
    <div className={`status-card ${status.connected ? 'connected' : 'disconnected'}`}>
      <div className="status-header">
        <h3>📊 Database Status</h3>
        <button onClick={onRefresh} className="refresh-btn">🔄</button>
      </div>
      
      {status.connected ? (
        <div className="status-details">
          <div className="status-indicator">
            <span className="indicator green"></span>
            <span>Connected</span>
          </div>
          <div className="metric">
            <strong>{status.total_plays?.toLocaleString()}</strong> total plays
          </div>
        </div>
      ) : (
        <div className="status-details">
          <div className="status-indicator">
            <span className="indicator red"></span>
            <span>Disconnected</span>
          </div>
          {status.error && <div className="error-msg">{status.error}</div>}
        </div>
      )}
    </div>
  );
};

// Query Input Component
const QueryInput = ({ onSubmit, isLoading, value, onChange }) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (value.trim() && !isLoading) {
      onSubmit(value.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="query-form">
      <div className="input-group">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Ask a question about NFL statistics..."
          className="query-input"
          disabled={isLoading}
        />
        <button 
          type="submit" 
          disabled={!value.trim() || isLoading}
          className="query-btn"
        >
          {isLoading ? '🔄' : '🔍'} Query
        </button>
      </div>
    </form>
  );
};

// Example Queries Component
const ExampleQueries = ({ onSelectExample, examples, isLoading }) => {
  return (
    <div className="examples-section">
      <h3>💡 Example Questions</h3>
      <div className="examples-grid">
        {examples.map((example, index) => (
          <button
            key={index}
            onClick={() => onSelectExample(example)}
            className="example-btn"
            disabled={isLoading}
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  );
};

// Results Table Component
const ResultsTable = ({ data, columns, timing, rowsReturned }) => {
  if (!data || data.length === 0) {
    return (
      <div className="no-results">
        <h3>No Results Found</h3>
        <p>Try adjusting your query parameters or check your spelling.</p>
      </div>
    );
  }

  const downloadCSV = () => {
    const headers = columns.join(',');
    const rows = data.map(row => 
      columns.map(col => {
        const value = row[col];
        return typeof value === 'string' && value.includes(',') 
          ? `"${value}"` 
          : value;
      }).join(',')
    );
    const csv = [headers, ...rows].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'nfl_query_results.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="results-section">
      <div className="results-header">
        <h3>📈 Results</h3>
        <div className="results-actions">
          <div className="timing-info">
            <span>⏱️ LLM: {timing.llm_time?.toFixed(2)}s</span>
            <span>🗄️ DB: {timing.db_time?.toFixed(3)}s</span>
            <span>📊 {rowsReturned} rows</span>
          </div>
          <button onClick={downloadCSV} className="download-btn">
            📥 Download CSV
          </button>
        </div>
      </div>
      
      <div className="table-container">
        <table className="results-table">
          <thead>
            <tr>
              {columns.map(col => (
                <th key={col}>{col.replace(/_/g, ' ').toUpperCase()}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr key={index}>
                {columns.map(col => (
                  <td key={col}>
                    {typeof row[col] === 'number' ? 
                      Number(row[col]).toLocaleString() : 
                      row[col]
                    }
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// SQL Query Display Component  
const SqlDisplay = ({ query, isVisible, onToggle }) => {
  if (!query) return null;
  
  return (
    <div className="sql-section">
      <button onClick={onToggle} className="sql-toggle">
        🔍 {isVisible ? 'Hide' : 'Show'} Generated SQL
      </button>
      {isVisible && (
        <pre className="sql-code">
          <code>{query}</code>
        </pre>
      )}
    </div>
  );
};

// Main App Component
const App = () => {
  const { user, token, logout, isAuthenticated } = useAuth();
  const [showLogin, setShowLogin] - useState(false);
  const [showRegister, setShowRegister] = useState(false)


  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [dbStatus, setDbStatus] = useState({ connected: false });
  const [examples, setExamples] = useState([]);
  const [showSql, setShowSql] = useState(false);

  const [selectedModel, setSelectedModel] = useState('gpt-oss'); // Default to gpt-oss
  const [availableModels, setAvailableModels] = useState([]);



  useEffect(() => {
    loadDbStatus();
    loadExamples();
    loadAvailableModels();
  }, []);



  const loadDbStatus = async () => {
    try {
      const status = await apiCall('/status');
      setDbStatus(status);
    } catch (err) {
      setDbStatus({ connected: false, error: err.message });
    }
  };

  const loadExamples = async () => {
    try {
      const response = await apiCall('/examples');
      setExamples(response.examples || []);
    } catch (err) {
      console.error('Failed to load examples:', err);
      // Fallback examples
      setExamples([
        "Top 5 QBs by passing yards",
        "Jared Goff completion percentage",
        "Third down conversion leaders",
        "Red zone touchdown percentage"
      ]);
    }
  };

  const loadAvailableModels = async () => {
    try {
      const response = await apiCall('/models');
      setAvailableModels(response.models || []);

      // Set default to first available model
      const availableModel = response.models.find(m => m.available);
      if (availableModel) {
        setSelectedModel(availableModel.id);
      }
    } catch (err) {
      console.error('Failed to load models:', err);
      // Fallback models
      setAvailableModels([
        { id: 'gpt-oss', name: 'GPT-OSS (Local)', available: true, cost: 'Free' }
      ]);
    }
  };

    const ModelSelector = () => {
    if (availableModels.length <= 1) return null;

    return (
      <div className="model-selector">
        <h3>🤖 Model Selection</h3>
        <div className="model-options">
          {availableModels.map(model => (
            <div key={model.id} className="model-option">
              <label className={`model-label ${!model.available ? 'unavailable' : ''}`}>
                <input
                  type="radio"
                  name="model"
                  value={model.id}
                  checked={selectedModel === model.id}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  disabled={!model.available || isLoading}
                />
                <div className="model-info">
                  <div className="model-name">
                    {model.name}
                    {!model.available && <span className="unavailable-tag">Unavailable</span>}
                  </div>
                  <div className="model-description">{model.description}</div>
                  <div className="model-cost">{model.cost}</div>
                </div>
              </label>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const executeQuery = async (queryText) => {
    if (!dbStatus.connected) {
      setError("Database is not connected. Please check the status.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setResults(null);
    
    try {
      const response = await apiCall('/query', {
        method: 'POST',
        body: JSON.stringify({
          question: queryText,
          include_sql: true,
          model: selectedModel
        })
      });
      
      if (response.success) {
        setResults(response);
      } else {
        setError(response.error || 'Query failed');
      }
    } catch (err) {
      setError(`Request failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (exampleQuery) => {
    setQuery(exampleQuery);
    executeQuery(exampleQuery);
  };

  return (
    <div className="App">
      <header className="app-header">
        <div className="hero-section">
          <h1>🏈 Ask Me NFL</h1>
          <p>Ask questions about NFL statistics in plain English!</p>
        </div>
      </header>

      <main className="app-main">
        <div className="layout">
          <div className="sidebar">
            <DatabaseStatus 
              status={dbStatus} 
              onRefresh={loadDbStatus} 
            />

            <ModelSelector />
            
            <ExampleQueries 
              examples={examples}
              onSelectExample={handleExampleClick}
              isLoading={isLoading}
            />
          </div>

          <div className="main-content">
            <QueryInput 
              onSubmit={executeQuery}
              isLoading={isLoading}
              value={query}
              onChange={setQuery}
            />

            {error && (
              <div className="error-message">
                <h3>❌ Error</h3>
                <p>{error}</p>
              </div>
            )}

            {isLoading && (
              <div className="loading-message">
                <div className="spinner"></div>
                <p>🤖 Processing your query...</p>
              </div>
            )}

            {results && results.success && (
              <>
                <ResultsTable 
                  data={results.data}
                  columns={results.columns}
                  timing={results.timing}
                  rowsReturned={results.rows_returned}
                />
                
                <SqlDisplay 
                  query={results.sql_query}
                  isVisible={showSql}
                  onToggle={() => setShowSql(!showSql)}
                />
              </>
            )}
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>Powered by FastAPI + React </p>
      </footer>
    </div>
  );
};




export default App;
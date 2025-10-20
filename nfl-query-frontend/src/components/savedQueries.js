import React, { useState, useEffect } from 'react';
import './savedQueries.css';

const API_BASE_URL = '/api';

const SavedQueries = ({ token, onLoadQuery, currentQuery, onQuerySaved }) => {
  const [savedQueries, setSavedQueries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState('');
  const [savingCurrent, setSavingCurrent] = useState(false);
  const [newQueryName, setNewQueryName] = useState('');

  useEffect(() => {
    if (token) {
      loadSavedQueries();
    }
  }, [token]);

  const loadSavedQueries = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/queries`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success) {
        setSavedQueries(data.queries || []);
      } else {
        setError(data.message || 'Failed to load queries');
      }
    } catch (err) {
      setError('Failed to load saved queries');
      console.error('Load queries error:', err);
    } finally {
      setLoading(false);
    }
  };

  const saveCurrentQuery = async () => {
    if (!currentQuery || !newQueryName.trim()) {
      setError('Please enter a name for the query');
      return;
    }

    setSavingCurrent(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/queries/save`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          queryText: currentQuery,
          queryName: newQueryName.trim()
        })
      });

      const data = await response.json();

      if (data.success) {
        setNewQueryName('');
        await loadSavedQueries();
        if (onQuerySaved) onQuerySaved();
      } else {
        setError(data.message || 'Failed to save query');
      }
    } catch (err) {
      setError('Failed to save query');
      console.error('Save query error:', err);
    } finally {
      setSavingCurrent(false);
    }
  };

  const updateQuery = async (queryId, newName) => {
    try {
      const response = await fetch(`${API_BASE_URL}/queries/${queryId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          queryText: query.queryContent,
          queryName: newName
        })
      });

      const data = await response.json();

      if (data.success) {
        await loadSavedQueries();
        setEditingId(null);
        setEditName('');
      } else {
        setError(data.message || 'Failed to update query');
      }
    } catch (err) {
      setError('Failed to update query');
      console.error('Update query error:', err);
    }
  };

  const deleteQuery = async (queryId) => {
    if (!window.confirm('Are you sure you want to delete this query?')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/queries/${queryId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success) {
        await loadSavedQueries();
      } else {
        setError(data.message || 'Failed to delete query');
      }
    } catch (err) {
      setError('Failed to delete query');
      console.error('Delete query error:', err);
    }
  };

  const startEdit = (query) => {
    setEditingId(query.id);
    setEditName(query.queryName || '');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditName('');
  };

  const saveEdit = (queryId) => {
    if (editName.trim()) {
      updateQuery(queryId, editName.trim());
    } else {
      cancelEdit();
    }
  };

  if (!token) {
    return null;
  }

  return (
    <div className="saved-queries-section">
      <div className="saved-queries-header">
        <h3>Saved Queries</h3>
        <button onClick={loadSavedQueries} className="refresh-btn" title="Refresh">
          🔄
        </button>
      </div>

      {error && (
        <div className="query-error">
          {error}
        </div>
      )}

      {currentQuery && (
        <div className="save-current-section">
          <input
            type="text"
            placeholder="Enter query name..."
            value={newQueryName}
            onChange={(e) => setNewQueryName(e.target.value)}
            className="query-name-input"
            onKeyPress={(e) => e.key === 'Enter' && saveCurrentQuery()}
          />
          <button
            onClick={saveCurrentQuery}
            disabled={savingCurrent || !newQueryName.trim()}
            className="save-query-btn"
          >
            {savingCurrent ? 'Saving...' : 'Save Current Query'}
          </button>
        </div>
      )}

      {loading ? (
        <div className="queries-loading">Loading saved queries...</div>
      ) : savedQueries.length === 0 ? (
        <div className="no-queries">
          <p>No saved queries yet.</p>
          <p className="hint">Run a query and save it above!</p>
        </div>
      ) : (
        <div className="queries-list">
          {savedQueries.map((query) => (
            <div key={query.id} className="query-item">
              {editingId === query.id ? (
                <div className="query-edit">
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="edit-input"
                    autoFocus
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') saveEdit(query.id);
                      if (e.key === 'Escape') cancelEdit();
                    }}
                  />
                  <div className="edit-actions">
                    <button onClick={() => saveEdit(query.id)} className="save-edit-btn">
                      ✓
                    </button>
                    <button onClick={cancelEdit} className="cancel-edit-btn">
                      ✕
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="query-content" onClick={() => onLoadQuery(query.queryContent)}>
                    <div className="query-name">
                      {query.queryName || 'Untitled Query'}
                    </div>
                    <div className="query-text">
                      {query.queryContent}
                    </div>
                    <div className="query-date">
                      {new Date(query.createdAt).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="query-actions">
                    <button
                      onClick={() => startEdit(query)}
                      className="edit-btn"
                      title="Edit name"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => deleteQuery(query.id)}
                      className="delete-btn"
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SavedQueries;
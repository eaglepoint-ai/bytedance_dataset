import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { resourceAPI } from '../api';
import { useAuth } from '../context/AuthContext';
import './Resources.css';

export const Resources = () => {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');
  
  const { isAdmin } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadResources();
  }, []);

  const loadResources = async () => {
    try {
      setLoading(true);
      const response = await resourceAPI.getAll();
      setResources(response.data.resources || []);
      setError('');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load resources');
    } finally {
      setLoading(false);
    }
  };

  const filteredResources = resources.filter(resource => {
    if (filter === 'active') return resource.status === 'active';
    if (filter === 'inactive') return resource.status === 'inactive';
    return true;
  });

  const handleCreateReservation = (resourceId) => {
    navigate(`/reservations/create?resource=${resourceId}`);
  };

  if (loading) {
    return <div className="loading">Loading resources...</div>;
  }

  return (
    <div className="resources-page">
      <div className="resources-header">
        <h2>Resources</h2>
        <div className="resources-actions">
          <select 
            value={filter} 
            onChange={(e) => setFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Resources</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive</option>
          </select>
          {isAdmin() && (
            <button 
              onClick={() => navigate('/resources/create')}
              className="btn-primary"
            >
              Create Resource
            </button>
          )}
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="resources-grid">
        {filteredResources.length === 0 ? (
          <div className="no-resources">No resources found</div>
        ) : (
          filteredResources.map((resource) => (
            <div key={resource.id} className="resource-card">
              <div className="resource-header">
                <h3>{resource.name}</h3>
                <span className={`status-badge ${resource.status === 'active' ? 'active' : 'inactive'}`}>
                  {resource.status === 'active' ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              <div className="resource-info">
                <p><strong>Type:</strong> {resource.type}</p>
                <p><strong>Location:</strong> {resource.location || 'N/A'}</p>
                {resource.capacity && (
                  <p><strong>Capacity:</strong> {resource.capacity}</p>
                )}
              </div>

              {resource.description && (
                <p className="resource-description">{resource.description}</p>
              )}

              <div className="resource-actions">
                {resource.status === 'active' && (
                  <button 
                    onClick={() => handleCreateReservation(resource.id)}
                    className="btn-primary btn-small"
                  >
                    Reserve
                  </button>
                )}
                {isAdmin() && (
                  <button 
                    onClick={() => navigate(`/resources/${resource.id}/edit`)}
                    className="btn-secondary btn-small"
                  >
                    Edit
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="back-button">
        <button onClick={() => navigate('/dashboard')} className="btn-secondary">
          Back to Dashboard
        </button>
      </div>
    </div>
  );
};

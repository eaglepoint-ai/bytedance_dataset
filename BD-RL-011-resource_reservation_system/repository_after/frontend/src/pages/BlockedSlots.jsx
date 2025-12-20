import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { reservationAPI, resourceAPI } from '../api';
import './BlockedSlots.css';

export const BlockedSlots = () => {
  const [resources, setResources] = useState([]);
  const [reservations, setReservations] = useState([]);
  const [formData, setFormData] = useState({
    resource_id: '',
    start_time: '',
    end_time: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [resourcesRes, reservationsRes] = await Promise.all([
        resourceAPI.getAll(),
        reservationAPI.getAll()
      ]);
      setResources((resourcesRes.data.resources || []).filter(r => r.status === 'active'));
      setReservations((reservationsRes.data.reservations || []).filter(r => r.status === 'blocked'));
    } catch (err) {
      setError('Failed to load data');
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const formatDateTimeForInput = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.resource_id || !formData.start_time || !formData.end_time) {
      setError('All fields are required');
      return;
    }

    const startDate = new Date(formData.start_time);
    const endDate = new Date(formData.end_time);

    if (startDate >= endDate) {
      setError('End time must be after start time');
      return;
    }

    if (startDate < new Date()) {
      setError('Start time must be in the future');
      return;
    }

    setLoading(true);

    try {
      const submitData = {
        resource_id: parseInt(formData.resource_id),
        start_time: startDate.toISOString(),
        end_time: endDate.toISOString()
      };

      await reservationAPI.createBlocked(submitData);
      setFormData({ resource_id: '', start_time: '', end_time: '' });
      await loadData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create blocked slot');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (id) => {
    if (!window.confirm('Are you sure you want to remove this blocked slot?')) {
      return;
    }

    try {
      setActionLoading(id);
      await reservationAPI.cancel(id);
      await loadData();
    } catch (err) {
      setError('Failed to remove blocked slot');
    } finally {
      setActionLoading(null);
    }
  };

  const getResourceName = (resourceId) => {
    const resource = resources.find(r => r.id === resourceId);
    return resource?.name || 'Unknown';
  };

  const formatDateTime = (isoString) => {
    return new Date(isoString).toLocaleString();
  };

  const getMinDateTime = () => {
    return formatDateTimeForInput(new Date());
  };

  return (
    <div className="blocked-slots-page">
      <h2>Manage Blocked Time Slots</h2>
      
      <div className="blocked-slots-content">
        <div className="create-section">
          <h3>Create Blocked Slot</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="resource_id">Resource *</label>
              <select
                id="resource_id"
                name="resource_id"
                value={formData.resource_id}
                onChange={handleChange}
                required
                disabled={loading}
              >
                <option value="">Select a resource</option>
                {resources.map((resource) => (
                  <option key={resource.id} value={resource.id}>
                    {resource.name} ({resource.type})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="start_time">Start Time *</label>
              <input
                id="start_time"
                name="start_time"
                type="datetime-local"
                value={formData.start_time}
                onChange={handleChange}
                min={getMinDateTime()}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="end_time">End Time *</label>
              <input
                id="end_time"
                name="end_time"
                type="datetime-local"
                value={formData.end_time}
                onChange={handleChange}
                min={formData.start_time || getMinDateTime()}
                required
                disabled={loading}
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Blocked Slot'}
            </button>
          </form>
        </div>

        <div className="list-section">
          <h3>Current Blocked Slots</h3>
          {reservations.length === 0 ? (
            <div className="no-data">No blocked slots found</div>
          ) : (
            <div className="blocked-list">
              {reservations.map((reservation) => (
                <div key={reservation.id} className="blocked-item">
                  <div className="blocked-info">
                    <h4>{getResourceName(reservation.resource_id)}</h4>
                    <p>{formatDateTime(reservation.start_time)} - {formatDateTime(reservation.end_time)}</p>
                  </div>
                  <button 
                    onClick={() => handleCancel(reservation.id)}
                    className="btn-danger btn-small"
                    disabled={actionLoading === reservation.id}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="back-button">
        <button onClick={() => navigate('/dashboard')} className="btn-secondary">
          Back to Dashboard
        </button>
      </div>
    </div>
  );
};

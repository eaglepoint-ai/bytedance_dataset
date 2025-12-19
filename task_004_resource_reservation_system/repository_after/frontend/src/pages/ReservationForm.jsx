import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { reservationAPI, resourceAPI } from '../api';
import './ReservationForm.css';

export const ReservationForm = () => {
  const [searchParams] = useSearchParams();
  const [resources, setResources] = useState([]);
  const [formData, setFormData] = useState({
    resource_id: searchParams.get('resource') || '',
    start_time: '',
    end_time: '',
    purpose: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();

  useEffect(() => {
    loadResources();
  }, []);

  const loadResources = async () => {
    try {
      const response = await resourceAPI.getAll();
      const activeResources = (response.data.resources || []).filter(r => r.status === 'active');
      setResources(activeResources);
    } catch (err) {
      setError('Failed to load resources');
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

    if (!formData.resource_id) {
      setError('Please select a resource');
      return;
    }

    if (!formData.start_time || !formData.end_time) {
      setError('Please select start and end times');
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
        end_time: endDate.toISOString(),
        purpose: formData.purpose.trim() || undefined
      };

      await reservationAPI.create(submitData);
      navigate('/reservations');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create reservation');
    } finally {
      setLoading(false);
    }
  };

  const getMinDateTime = () => {
    return formatDateTimeForInput(new Date());
  };

  return (
    <div className="form-page">
      <div className="form-container">
        <h2>Create Reservation</h2>
        
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

          <div className="form-group">
            <label htmlFor="purpose">Purpose</label>
            <textarea
              id="purpose"
              name="purpose"
              value={formData.purpose}
              onChange={handleChange}
              disabled={loading}
              rows={4}
              placeholder="Optional: Describe the purpose of this reservation"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="form-actions">
            <button 
              type="button" 
              onClick={() => navigate('/reservations')}
              className="btn-secondary"
              disabled={loading}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create Reservation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { reservationAPI, resourceAPI } from '../api';
import { useAuth } from '../context/AuthContext';
import './Reservations.css';

export const Reservations = () => {
  const [reservations, setReservations] = useState([]);
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(null);
  
  const { isAdmin } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [reservationsRes, resourcesRes] = await Promise.all([
        reservationAPI.getAll(),
        resourceAPI.getAll()
      ]);
      setReservations(reservationsRes.data.reservations || []);
      setResources(resourcesRes.data.resources || []);
      setError('');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const getResourceName = (resourceId) => {
    const resource = resources.find(r => r.id === resourceId);
    return resource?.name || 'Unknown';
  };

  const formatDateTime = (isoString) => {
    return new Date(isoString).toLocaleString();
  };

  const handleApprove = async (id) => {
    try {
      setActionLoading(id);
      await reservationAPI.approve(id);
      await loadData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to approve reservation');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (id) => {
    try {
      setActionLoading(id);
      await reservationAPI.reject(id);
      await loadData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to reject reservation');
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancel = async (id) => {
    if (!window.confirm('Are you sure you want to cancel this reservation?')) {
      return;
    }

    try {
      setActionLoading(id);
      await reservationAPI.cancel(id);
      await loadData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to cancel reservation');
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'warning',
      approved: 'success',
      rejected: 'danger',
      cancelled: 'secondary',
      completed: 'info',
      blocked: 'blocked'
    };
    return colors[status] || 'secondary';
  };

  if (loading) {
    return <div className="loading">Loading reservations...</div>;
  }

  return (
    <div className="reservations-page">
      <div className="reservations-header">
        <h2>{isAdmin() ? 'All Reservations' : 'My Reservations'}</h2>
        <button 
          onClick={() => navigate('/reservations/create')}
          className="btn-primary"
        >
          New Reservation
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="reservations-list">
        {reservations.length === 0 ? (
          <div className="no-data">No reservations found</div>
        ) : (
          reservations.map((reservation) => (
            <div key={reservation.id} className="reservation-card">
              <div className="reservation-header">
                <div>
                  <h3>{getResourceName(reservation.resource_id)}</h3>
                  {reservation.purpose && (
                    <p className="reservation-purpose">{reservation.purpose}</p>
                  )}
                </div>
                <span className={`status-badge ${getStatusColor(reservation.status)}`}>
                  {reservation.status}
                </span>
              </div>

              <div className="reservation-info">
                <div className="info-row">
                  <span className="label">Start:</span>
                  <span>{formatDateTime(reservation.start_time)}</span>
                </div>
                <div className="info-row">
                  <span className="label">End:</span>
                  <span>{formatDateTime(reservation.end_time)}</span>
                </div>
                {isAdmin() && (
                  <div className="info-row">
                    <span className="label">User:</span>
                    <span>{reservation.user_email || 'N/A'}</span>
                  </div>
                )}
              </div>

              <div className="reservation-actions">
                {isAdmin() && reservation.status === 'pending' && (
                  <>
                    <button 
                      onClick={() => handleApprove(reservation.id)}
                      className="btn-success btn-small"
                      disabled={actionLoading === reservation.id}
                    >
                      Approve
                    </button>
                    <button 
                      onClick={() => handleReject(reservation.id)}
                      className="btn-danger btn-small"
                      disabled={actionLoading === reservation.id}
                    >
                      Reject
                    </button>
                  </>
                )}
                {(reservation.status === 'pending' || reservation.status === 'approved') && (
                  <button 
                    onClick={() => handleCancel(reservation.id)}
                    className="btn-secondary btn-small"
                    disabled={actionLoading === reservation.id}
                  >
                    Cancel
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

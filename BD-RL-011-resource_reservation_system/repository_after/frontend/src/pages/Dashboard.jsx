import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css';

export const Dashboard = () => {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="dashboard">
      <nav className="dashboard-nav">
        <div className="nav-brand">
          <h1>Resource Reservation</h1>
        </div>
        <div className="nav-user">
          <span>{user?.name} ({user?.role})</span>
          <button onClick={handleLogout} className="btn-secondary">
            Logout
          </button>
        </div>
      </nav>

      <div className="dashboard-content">
        <div className="dashboard-sidebar">
          <button 
            onClick={() => navigate('/dashboard')}
            className="sidebar-link active"
          >
            {isAdmin() ? 'Admin Dashboard' : 'My Reservations'}
          </button>
          <button 
            onClick={() => navigate('/resources')}
            className="sidebar-link"
          >
            Resources
          </button>
          <button 
            onClick={() => navigate('/reservations')}
            className="sidebar-link"
          >
            {isAdmin() ? 'All Reservations' : 'My Reservations'}
          </button>
          {isAdmin() && (
            <>
              <button 
                onClick={() => navigate('/resources/create')}
                className="sidebar-link"
              >
                Create Resource
              </button>
              <button 
                onClick={() => navigate('/blocked-slots')}
                className="sidebar-link"
              >
                Blocked Slots
              </button>
            </>
          )}
        </div>

        <div className="dashboard-main">
          <h2>Welcome, {user?.name}</h2>
          <div className="dashboard-cards">
            <div className="dashboard-card">
              <h3>Resources</h3>
              <p>View and manage available resources</p>
              <button 
                onClick={() => navigate('/resources')}
                className="btn-primary"
              >
                View Resources
              </button>
            </div>

            <div className="dashboard-card">
              <h3>Reservations</h3>
              <p>{isAdmin() ? 'Manage all reservations' : 'View your reservations'}</p>
              <button 
                onClick={() => navigate('/reservations')}
                className="btn-primary"
              >
                View Reservations
              </button>
            </div>

            {isAdmin() && (
              <div className="dashboard-card">
                <h3>Admin Tools</h3>
                <p>Create resources and block time slots</p>
                <button 
                  onClick={() => navigate('/resources/create')}
                  className="btn-primary"
                >
                  Admin Panel
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

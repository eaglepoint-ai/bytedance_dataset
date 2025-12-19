import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { Resources } from './pages/Resources';
import { ResourceForm } from './pages/ResourceForm';
import { Reservations } from './pages/Reservations';
import { ReservationForm } from './pages/ReservationForm';
import { BlockedSlots } from './pages/BlockedSlots';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/resources" 
            element={
              <ProtectedRoute>
                <Resources />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/resources/create" 
            element={
              <ProtectedRoute adminOnly>
                <ResourceForm />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/resources/:id/edit" 
            element={
              <ProtectedRoute adminOnly>
                <ResourceForm isEdit />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/reservations" 
            element={
              <ProtectedRoute>
                <Reservations />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/reservations/create" 
            element={
              <ProtectedRoute>
                <ReservationForm />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/blocked-slots" 
            element={
              <ProtectedRoute adminOnly>
                <BlockedSlots />
              </ProtectedRoute>
            } 
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;

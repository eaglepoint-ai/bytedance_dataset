import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '../../../repository_after/frontend/src/components/ProtectedRoute.jsx';
import { AuthProvider } from '../../../repository_after/frontend/src/context/AuthContext.jsx';

// Mock the auth API
vi.mock('../../../repository_after/frontend/src/api/index.js', () => ({
  authAPI: {
    login: vi.fn(),
    register: vi.fn()
  }
}));

const TestApp = ({ user, loading = false, adminOnly = false }) => {
  // Mock the context directly by setting localStorage
  if (user) {
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('token', 'test-token');
  }

  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/dashboard" element={<div>Dashboard Page</div>} />
          <Route
            path="/protected"
            element={
              <ProtectedRoute adminOnly={adminOnly}>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('ProtectedRoute Component', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should show loading state while loading', async () => {
    // Set up loading state by not setting localStorage
    render(
      <BrowserRouter>
        <AuthProvider>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </AuthProvider>
      </BrowserRouter>
    );

    // Initially shows loading (briefly)
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should redirect to login when user is not authenticated', async () => {
    render(<TestApp user={null} />);

    // Wait for loading to complete
    await screen.findByText('Login Page');
    expect(screen.getByText('Login Page')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('should render children when user is authenticated', async () => {
    const mockUser = { id: 1, email: 'test@test.com', role: 'user' };
    render(<TestApp user={mockUser} />);

    // Wait for auth to initialize
    await screen.findByText('Protected Content');
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('should allow admin user to access admin-only routes', async () => {
    const mockAdmin = { id: 1, email: 'admin@test.com', role: 'admin' };
    render(<TestApp user={mockAdmin} adminOnly={true} />);

    await screen.findByText('Protected Content');
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('should redirect non-admin user to dashboard for admin-only routes', async () => {
    const mockUser = { id: 1, email: 'test@test.com', role: 'user' };
    render(<TestApp user={mockUser} adminOnly={true} />);

    await screen.findByText('Dashboard Page');
    expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('should allow regular user to access non-admin routes', async () => {
    const mockUser = { id: 1, email: 'test@test.com', role: 'user' };
    render(<TestApp user={mockUser} adminOnly={false} />);

    await screen.findByText('Protected Content');
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });
});

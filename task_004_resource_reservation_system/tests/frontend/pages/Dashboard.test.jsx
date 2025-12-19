import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Dashboard } from '../../../repository_after/frontend/src/pages/Dashboard.jsx';
import { AuthProvider } from '../../../repository_after/frontend/src/context/AuthContext.jsx';

// Mock the API module
vi.mock('../../../repository_after/frontend/src/api/index.js', () => ({
  authAPI: {
    login: vi.fn(),
    register: vi.fn()
  }
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate
  };
});

const renderDashboard = (user) => {
  if (user) {
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('token', 'test-token');
  }

  return render(
    <BrowserRouter>
      <AuthProvider>
        <Dashboard />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('Dashboard Page', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    mockNavigate.mockClear();
  });

  describe('Regular User Dashboard', () => {
    const regularUser = { id: 1, name: 'John Doe', email: 'user@test.com', role: 'user' };

    it('should render dashboard with user info', async () => {
      renderDashboard(regularUser);

      await waitFor(() => {
        expect(screen.getByText(/Welcome, John Doe/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/John Doe \(user\)/)).toBeInTheDocument();
    });

    it('should show regular user menu items', async () => {
      renderDashboard(regularUser);

      await waitFor(() => {
        expect(screen.getByText('My Reservations')).toBeInTheDocument();
      });

      expect(screen.getByText('Resources')).toBeInTheDocument();
      expect(screen.queryByText('Create Resource')).not.toBeInTheDocument();
      expect(screen.queryByText('Blocked Slots')).not.toBeInTheDocument();
    });

    it('should show user dashboard cards', async () => {
      renderDashboard(regularUser);

      await waitFor(() => {
        expect(screen.getByText('Resources')).toBeInTheDocument();
      });

      expect(screen.getByText('View and manage available resources')).toBeInTheDocument();
      expect(screen.getByText('View your reservations')).toBeInTheDocument();
      expect(screen.queryByText('Admin Tools')).not.toBeInTheDocument();
    });

    it('should navigate to resources page', async () => {
      renderDashboard(regularUser);

      await waitFor(() => {
        expect(screen.getByText('Resources')).toBeInTheDocument();
      });

      const resourceButtons = screen.getAllByText(/View Resources|Resources/i);
      fireEvent.click(resourceButtons[0]);

      expect(mockNavigate).toHaveBeenCalledWith('/resources');
    });

    it('should navigate to reservations page', async () => {
      renderDashboard(regularUser);

      await waitFor(() => {
        expect(screen.getByText('Reservations')).toBeInTheDocument();
      });

      const reservationButtons = screen.getAllByText(/View Reservations|My Reservations/i);
      fireEvent.click(reservationButtons[0]);

      expect(mockNavigate).toHaveBeenCalledWith('/reservations');
    });

    it('should handle logout', async () => {
      renderDashboard(regularUser);

      await waitFor(() => {
        expect(screen.getByText('Logout')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Logout'));

      expect(mockNavigate).toHaveBeenCalledWith('/login');
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });
  });

  describe('Admin User Dashboard', () => {
    const adminUser = { id: 2, name: 'Admin User', email: 'admin@test.com', role: 'admin' };

    it('should render dashboard with admin info', async () => {
      renderDashboard(adminUser);

      await waitFor(() => {
        expect(screen.getByText(/Welcome, Admin User/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Admin User \(admin\)/)).toBeInTheDocument();
    });

    it('should show admin menu items', async () => {
      renderDashboard(adminUser);

      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      });

      expect(screen.getByText('Resources')).toBeInTheDocument();
      expect(screen.getByText('All Reservations')).toBeInTheDocument();
      expect(screen.getByText('Create Resource')).toBeInTheDocument();
      expect(screen.getByText('Blocked Slots')).toBeInTheDocument();
    });

    it('should show admin dashboard cards', async () => {
      renderDashboard(adminUser);

      await waitFor(() => {
        expect(screen.getByText('Admin Tools')).toBeInTheDocument();
      });

      expect(screen.getByText('Manage all reservations')).toBeInTheDocument();
      expect(screen.getByText('Create resources and block time slots')).toBeInTheDocument();
    });

    it('should navigate to create resource page', async () => {
      renderDashboard(adminUser);

      await waitFor(() => {
        expect(screen.getByText('Create Resource')).toBeInTheDocument();
      });

      // Click sidebar Create Resource button
      const createButtons = screen.getAllByText('Create Resource');
      fireEvent.click(createButtons[0]);

      expect(mockNavigate).toHaveBeenCalledWith('/resources/create');
    });

    it('should navigate to blocked slots page', async () => {
      renderDashboard(adminUser);

      await waitFor(() => {
        expect(screen.getByText('Blocked Slots')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Blocked Slots'));

      expect(mockNavigate).toHaveBeenCalledWith('/blocked-slots');
    });

    it('should navigate to admin panel from card', async () => {
      renderDashboard(adminUser);

      await waitFor(() => {
        expect(screen.getByText('Admin Panel')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Admin Panel'));

      expect(mockNavigate).toHaveBeenCalledWith('/resources/create');
    });

    it('should navigate to dashboard home', async () => {
      renderDashboard(adminUser);

      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Admin Dashboard'));

      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });
});

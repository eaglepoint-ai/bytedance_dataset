import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../../../repository_after/frontend/src/context/AuthContext.jsx';
import * as authAPIModule from '../../../repository_after/frontend/src/api/index.js';

// Mock the API module
vi.mock('../../../repository_after/frontend/src/api/index.js', () => ({
  authAPI: {
    login: vi.fn(),
    register: vi.fn()
  }
}));

// Test component to access context
const TestComponent = () => {
  const { user, login, register, logout, isAdmin, loading } = useAuth();
  
  return (
    <div>
      <div data-testid="loading">{loading ? 'loading' : 'ready'}</div>
      <div data-testid="user">{user ? JSON.stringify(user) : 'null'}</div>
      <div data-testid="is-admin">{isAdmin() ? 'admin' : 'not-admin'}</div>
      <button onClick={() => login('test@test.com', 'password')}>Login</button>
      <button onClick={() => register('Test', 'test@test.com', 'password')}>Register</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('useAuth Hook', () => {
    it('should throw error when used outside AuthProvider', () => {
      // Suppress console.error for this test
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      expect(() => {
        render(<TestComponent />);
      }).toThrow('useAuth must be used within AuthProvider');
      
      consoleError.mockRestore();
    });
  });

  describe('AuthProvider', () => {
    it('should initialize with no user when localStorage is empty', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(screen.getByTestId('is-admin')).toHaveTextContent('not-admin');
    });

    it('should initialize with user from localStorage', async () => {
      const mockUser = { id: 1, email: 'test@test.com', role: 'user' };
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('token', 'test-token');

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      expect(screen.getByTestId('user')).toHaveTextContent(JSON.stringify(mockUser));
      expect(screen.getByTestId('is-admin')).toHaveTextContent('not-admin');
    });

    it('should initialize with admin user from localStorage', async () => {
      const mockUser = { id: 1, email: 'admin@test.com', role: 'admin' };
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('token', 'admin-token');

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      expect(screen.getByTestId('user')).toHaveTextContent(JSON.stringify(mockUser));
      expect(screen.getByTestId('is-admin')).toHaveTextContent('admin');
    });

    it('should handle login successfully', async () => {
      const mockUser = { id: 1, email: 'test@test.com', role: 'user' };
      const mockResponse = {
        data: {
          user: mockUser,
          token: 'new-token'
        }
      };

      authAPIModule.authAPI.login.mockResolvedValue(mockResponse);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      await act(async () => {
        screen.getByText('Login').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent(JSON.stringify(mockUser));
      });

      expect(localStorage.getItem('token')).toBe('new-token');
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockUser));
      expect(authAPIModule.authAPI.login).toHaveBeenCalledWith({
        email: 'test@test.com',
        password: 'password'
      });
    });

    it('should handle register successfully', async () => {
      const mockUser = { id: 1, email: 'test@test.com', name: 'Test', role: 'user' };
      const mockResponse = {
        data: {
          user: mockUser,
          token: 'new-token'
        }
      };

      authAPIModule.authAPI.register.mockResolvedValue(mockResponse);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      await act(async () => {
        screen.getByText('Register').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent(JSON.stringify(mockUser));
      });

      expect(localStorage.getItem('token')).toBe('new-token');
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockUser));
      expect(authAPIModule.authAPI.register).toHaveBeenCalledWith({
        name: 'Test',
        email: 'test@test.com',
        password: 'password',
        role: 'user'
      });
    });

    it('should handle logout', async () => {
      const mockUser = { id: 1, email: 'test@test.com', role: 'user' };
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('token', 'test-token');

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      expect(screen.getByTestId('user')).toHaveTextContent(JSON.stringify(mockUser));

      await act(async () => {
        screen.getByText('Logout').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('null');
      });

      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });

    it('should handle login error', async () => {
      authAPIModule.authAPI.login.mockRejectedValue(new Error('Login failed'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      await expect(async () => {
        await act(async () => {
          screen.getByText('Login').click();
        });
      }).rejects.toThrow('Login failed');

      expect(screen.getByTestId('user')).toHaveTextContent('null');
    });

    it('should handle register error', async () => {
      authAPIModule.authAPI.register.mockRejectedValue(new Error('Registration failed'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      await expect(async () => {
        await act(async () => {
          screen.getByText('Register').click();
        });
      }).rejects.toThrow('Registration failed');

      expect(screen.getByTestId('user')).toHaveTextContent('null');
    });
  });
});

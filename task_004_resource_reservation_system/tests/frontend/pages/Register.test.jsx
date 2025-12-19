import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Register } from '../../../repository_after/frontend/src/pages/Register.jsx';
import { AuthProvider } from '../../../repository_after/frontend/src/context/AuthContext.jsx';
import * as authAPIModule from '../../../repository_after/frontend/src/api/index.js';

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

const renderRegister = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Register />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('Register Page', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    mockNavigate.mockClear();
  });

  it('should render register form', () => {
    renderRegister();

    expect(screen.getByText('Register')).toBeInTheDocument();
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument();
  });

  it('should show login link', () => {
    renderRegister();

    expect(screen.getByText(/Already have an account/i)).toBeInTheDocument();
    expect(screen.getByText('Login')).toBeInTheDocument();
  });

  it('should show password requirement hint', () => {
    renderRegister();

    expect(screen.getByText('At least 6 characters')).toBeInTheDocument();
  });

  it('should update name input', () => {
    renderRegister();

    const nameInput = screen.getByLabelText('Name');
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });

    expect(nameInput).toHaveValue('John Doe');
  });

  it('should update email input', () => {
    renderRegister();

    const emailInput = screen.getByLabelText('Email');
    fireEvent.change(emailInput, { target: { value: 'test@test.com' } });

    expect(emailInput).toHaveValue('test@test.com');
  });

  it('should update password input', () => {
    renderRegister();

    const passwordInput = screen.getByLabelText('Password');
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    expect(passwordInput).toHaveValue('password123');
  });

  it('should show error for short password', async () => {
    renderRegister();

    fireEvent.change(screen.getByLabelText('Name'), {
      target: { value: 'John Doe' }
    });
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@test.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: '12345' }
    });

    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText('Password must be at least 6 characters')).toBeInTheDocument();
    });

    expect(authAPIModule.authAPI.register).not.toHaveBeenCalled();
  });

  it('should handle successful registration', async () => {
    const mockUser = { id: 1, name: 'John Doe', email: 'test@test.com', role: 'user' };
    authAPIModule.authAPI.register.mockResolvedValue({
      data: {
        user: mockUser,
        token: 'test-token'
      }
    });

    renderRegister();

    fireEvent.change(screen.getByLabelText('Name'), {
      target: { value: 'John Doe' }
    });
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@test.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' }
    });

    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(authAPIModule.authAPI.register).toHaveBeenCalledWith({
        name: 'John Doe',
        email: 'test@test.com',
        password: 'password123',
        role: 'user'
      });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('should show error message on registration failure', async () => {
    authAPIModule.authAPI.register.mockRejectedValue({
      response: {
        data: {
          error: 'Email already exists'
        }
      }
    });

    renderRegister();

    fireEvent.change(screen.getByLabelText('Name'), {
      target: { value: 'John Doe' }
    });
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'existing@test.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' }
    });

    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument();
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should show generic error message when error response has no message', async () => {
    authAPIModule.authAPI.register.mockRejectedValue({
      response: {}
    });

    renderRegister();

    fireEvent.change(screen.getByLabelText('Name'), {
      target: { value: 'John Doe' }
    });
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@test.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' }
    });

    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText('Registration failed')).toBeInTheDocument();
    });
  });

  it('should disable form during registration', async () => {
    authAPIModule.authAPI.register.mockImplementation(() => new Promise(() => {}));

    renderRegister();

    fireEvent.change(screen.getByLabelText('Name'), {
      target: { value: 'John Doe' }
    });
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@test.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' }
    });

    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByLabelText('Name')).toBeDisabled();
      expect(screen.getByLabelText('Email')).toBeDisabled();
      expect(screen.getByLabelText('Password')).toBeDisabled();
      expect(screen.getByRole('button')).toBeDisabled();
      expect(screen.getByText('Registering...')).toBeInTheDocument();
    });
  });

  it('should clear error when submitting again', async () => {
    authAPIModule.authAPI.register.mockRejectedValueOnce({
      response: { data: { error: 'Email already exists' } }
    });

    renderRegister();

    // First attempt - fail
    fireEvent.change(screen.getByLabelText('Name'), {
      target: { value: 'John Doe' }
    });
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'existing@test.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' }
    });

    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument();
    });

    // Second attempt
    authAPIModule.authAPI.register.mockResolvedValueOnce({
      data: {
        user: { id: 1, name: 'John Doe', email: 'new@test.com', role: 'user' },
        token: 'test-token'
      }
    });

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'new@test.com' }
    });

    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.queryByText('Email already exists')).not.toBeInTheDocument();
    });
  });

  it('should have minimum length validation on password input', () => {
    renderRegister();

    const passwordInput = screen.getByLabelText('Password');
    expect(passwordInput).toHaveAttribute('minLength', '6');
  });
});

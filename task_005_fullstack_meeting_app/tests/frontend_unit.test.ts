/**
 * Frontend Unit Tests - API Client & Auth Logic
 * Tests REAL execution of frontend logic (not file existence)
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock environment variables
vi.stubGlobal('import', {
  meta: {
    env: {
      VITE_API_BASE_URL: 'http://localhost:8000',
      VITE_AUTH_BASE_URL: 'http://localhost:3001',
    },
  },
});

// Import after mocking environment
import { apiFetch } from '../repository_after/meeting-scheduler/web/src/api/client';
import { authFetch, login, register, logout, getSession } from '../repository_after/meeting-scheduler/web/src/lib/auth';

describe('API Client (client.ts)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('apiFetch uses credentials: "include"', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ success: true }),
    });

    await apiFetch('/api/test');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/test',
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('apiFetch resolves base URL from import.meta.env', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({}),
    });

    await apiFetch('/api/slots');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/slots',
      expect.any(Object)
    );
  });

  it('apiFetch throws on non-OK responses with detail message', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      text: async () => JSON.stringify({ detail: 'Invalid slot ID' }),
    });

    await expect(apiFetch('/api/meetings')).rejects.toThrow('Invalid slot ID');
  });

  it('apiFetch throws with status code on error', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      text: async () => JSON.stringify({ detail: 'Not found' }),
    });

    try {
      await apiFetch('/api/nonexistent');
    } catch (err: any) {
      expect(err.status).toBe(404);
      expect(err.message).toBe('Not found');
    }
  });

  it('apiFetch handles network errors', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(apiFetch('/api/test')).rejects.toThrow('Unable to connect to server');
  });

  it('apiFetch includes Content-Type: application/json header', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => '{}',
    });

    await apiFetch('/api/test', { method: 'POST' });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    );
  });
});

describe('Auth Helpers (auth.ts)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('authFetch uses credentials: "include"', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => '{}',
    });

    await authFetch('/api/auth/session');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:3001/api/auth/session',
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('login() calls POST /api/auth/login with credentials', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ user: { email: 'test@example.com' } }),
    });

    await login('test@example.com', 'password123');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:3001/api/auth/login',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'test@example.com', password: 'password123' }),
      })
    );
  });

  it('register() calls POST /api/auth/register with role', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ success: true }),
    });

    await register('new@example.com', 'pass123', 'consultant');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:3001/api/auth/register',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'new@example.com', password: 'pass123', role: 'consultant' }),
      })
    );
  });

  it('register() defaults role to "user"', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => '{}',
    });

    await register('user@example.com', 'password');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: expect.stringContaining('"role":"user"'),
      })
    );
  });

  it('logout() calls POST /api/auth/logout', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => '{}',
    });

    await logout();

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:3001/api/auth/logout',
      expect.objectContaining({
        method: 'POST',
      })
    );
  });

  it('getSession() returns null on 401 without throwing', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      text: async () => JSON.stringify({ error: 'Not authenticated' }),
    });

    const result = await getSession();

    expect(result).toBeNull();
  });

  it('getSession() returns user data on success', async () => {
    const mockUser = { id: '123', email: 'user@example.com', role: 'user' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ user: mockUser }),
    });

    const result = await getSession();

    expect(result).toEqual({ user: mockUser });
  });

  it('getSession() throws on non-401 errors', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      text: async () => JSON.stringify({ error: 'Server error' }),
    });

    await expect(getSession()).rejects.toThrow();
  });
});


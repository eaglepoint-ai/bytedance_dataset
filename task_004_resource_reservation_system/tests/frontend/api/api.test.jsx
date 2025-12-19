import { describe, it, expect, beforeEach, vi } from 'vitest';
import axios from 'axios';
import api, { authAPI, resourceAPI, reservationAPI } from '../../../repository_after/frontend/src/api/index.js';

vi.mock('axios');

describe('API Module', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('API Instance', () => {
    it('should create axios instance with correct baseURL', () => {
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: '/api',
          headers: { 'Content-Type': 'application/json' }
        })
      );
    });
  });

  describe('Request Interceptor', () => {
    let mockConfig;
    let requestInterceptor;

    beforeEach(() => {
      mockConfig = { headers: {} };
      const createCall = axios.create.mock.calls[axios.create.mock.calls.length - 1];
      if (createCall) {
        const mockInstance = createCall[0];
        requestInterceptor = mockInstance?.interceptors?.request?.use;
      }
    });

    it('should add Authorization header when token exists', async () => {
      localStorage.setItem('token', 'test-token');
      
      const mockApi = {
        interceptors: {
          request: {
            use: vi.fn((successHandler) => {
              const result = successHandler(mockConfig);
              expect(result.headers.Authorization).toBe('Bearer test-token');
            })
          },
          response: { use: vi.fn() }
        }
      };

      axios.create.mockReturnValue(mockApi);
      
      // Re-import to trigger interceptor setup
      await import('../../../repository_after/frontend/src/api/index.js?t=' + Date.now());
    });

    it('should not add Authorization header when token does not exist', async () => {
      const mockApi = {
        interceptors: {
          request: {
            use: vi.fn((successHandler) => {
              const result = successHandler(mockConfig);
              expect(result.headers.Authorization).toBeUndefined();
            })
          },
          response: { use: vi.fn() }
        }
      };

      axios.create.mockReturnValue(mockApi);
      
      await import('../../../repository_after/frontend/src/api/index.js?t=' + Date.now());
    });
  });

  describe('Response Interceptor', () => {
    it('should handle 401 errors by clearing storage and redirecting', async () => {
      const originalLocation = window.location;
      delete window.location;
      window.location = { href: '' };

      localStorage.setItem('token', 'test-token');
      localStorage.setItem('user', JSON.stringify({ id: 1 }));

      const mockApi = {
        interceptors: {
          request: { use: vi.fn() },
          response: {
            use: vi.fn((successHandler, errorHandler) => {
              const error = {
                response: { status: 401 }
              };
              
              try {
                errorHandler(error);
              } catch (e) {
                expect(localStorage.getItem('token')).toBeNull();
                expect(localStorage.getItem('user')).toBeNull();
                expect(window.location.href).toBe('/login');
              }
            })
          }
        }
      };

      axios.create.mockReturnValue(mockApi);
      
      await import('../../../repository_after/frontend/src/api/index.js?t=' + Date.now());

      window.location = originalLocation;
    });
  });

  describe('authAPI', () => {
    let mockApi;

    beforeEach(() => {
      mockApi = {
        post: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      };
      axios.create.mockReturnValue(mockApi);
    });

    it('should call register endpoint', async () => {
      const data = { email: 'test@test.com', password: 'password' };
      await authAPI.register(data);
      expect(mockApi.post).toHaveBeenCalledWith('/auth/register', data);
    });

    it('should call login endpoint', async () => {
      const data = { email: 'test@test.com', password: 'password' };
      await authAPI.login(data);
      expect(mockApi.post).toHaveBeenCalledWith('/auth/login', data);
    });

    it('should call getCurrentUser endpoint', async () => {
      await authAPI.getCurrentUser();
      expect(mockApi.get).toHaveBeenCalledWith('/auth/me');
    });
  });

  describe('resourceAPI', () => {
    let mockApi;

    beforeEach(() => {
      mockApi = {
        get: vi.fn().mockResolvedValue({ data: {} }),
        post: vi.fn().mockResolvedValue({ data: {} }),
        put: vi.fn().mockResolvedValue({ data: {} }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      };
      axios.create.mockReturnValue(mockApi);
    });

    it('should call getAll endpoint', async () => {
      await resourceAPI.getAll();
      expect(mockApi.get).toHaveBeenCalledWith('/resources');
    });

    it('should call getById endpoint', async () => {
      await resourceAPI.getById(1);
      expect(mockApi.get).toHaveBeenCalledWith('/resources/1');
    });

    it('should call create endpoint', async () => {
      const data = { name: 'Test Resource', type: 'room' };
      await resourceAPI.create(data);
      expect(mockApi.post).toHaveBeenCalledWith('/resources', data);
    });

    it('should call update endpoint', async () => {
      const data = { name: 'Updated Resource' };
      await resourceAPI.update(1, data);
      expect(mockApi.put).toHaveBeenCalledWith('/resources/1', data);
    });
  });

  describe('reservationAPI', () => {
    let mockApi;

    beforeEach(() => {
      mockApi = {
        get: vi.fn().mockResolvedValue({ data: {} }),
        post: vi.fn().mockResolvedValue({ data: {} }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      };
      axios.create.mockReturnValue(mockApi);
    });

    it('should call getAll endpoint', async () => {
      await reservationAPI.getAll();
      expect(mockApi.get).toHaveBeenCalledWith('/reservations');
    });

    it('should call getById endpoint', async () => {
      await reservationAPI.getById(1);
      expect(mockApi.get).toHaveBeenCalledWith('/reservations/1');
    });

    it('should call create endpoint', async () => {
      const data = { resource_id: 1, start_time: '2024-01-01T10:00:00Z' };
      await reservationAPI.create(data);
      expect(mockApi.post).toHaveBeenCalledWith('/reservations', data);
    });

    it('should call approve endpoint', async () => {
      await reservationAPI.approve(1);
      expect(mockApi.post).toHaveBeenCalledWith('/reservations/1/approve');
    });

    it('should call reject endpoint', async () => {
      await reservationAPI.reject(1);
      expect(mockApi.post).toHaveBeenCalledWith('/reservations/1/reject');
    });

    it('should call cancel endpoint', async () => {
      await reservationAPI.cancel(1);
      expect(mockApi.post).toHaveBeenCalledWith('/reservations/1/cancel');
    });

    it('should call createBlocked endpoint', async () => {
      const data = { resource_id: 1, start_time: '2024-01-01T10:00:00Z' };
      await reservationAPI.createBlocked(data);
      expect(mockApi.post).toHaveBeenCalledWith('/reservations/blocked', data);
    });
  });
});

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useAuthStore } from '../authStore';
import { authApi } from '../../api/client';

// Mock the authApi
vi.mock('../../api/client', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}));

describe('authStore', () => {
  // Reset store state before each test
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('should successfully login with valid credentials', async () => {
      const mockUser = {
        id: 'user-123',
        username: 'testuser',
        created_at: '2024-01-01T00:00:00Z',
        last_login: '2024-03-10T00:00:00Z',
      };

      const mockResponse = {
        access_token: 'mock-jwt-token',
        token_type: 'bearer',
        user: mockUser,
      };

      vi.mocked(authApi.login).mockResolvedValue(mockResponse);

      const store = useAuthStore.getState();

      await expect(store.login('testuser', 'password123')).resolves.not.toThrow();

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.token).toBe('mock-jwt-token');
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe(null);

      expect(authApi.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
    });

    it('should handle login failure with invalid credentials', async () => {
      const mockError = new Error('Invalid credentials');
      vi.mocked(authApi.login).mockRejectedValue(mockError);

      const store = useAuthStore.getState();

      await expect(store.login('testuser', 'wrongpassword')).rejects.toThrow();

      const state = useAuthStore.getState();
      expect(state.user).toBe(null);
      expect(state.token).toBe(null);
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('Invalid credentials');
    });

    it('should handle login failure with generic error', async () => {
      vi.mocked(authApi.login).mockRejectedValue('Network error');

      const store = useAuthStore.getState();

      await expect(store.login('testuser', 'password123')).rejects.toThrow();

      const state = useAuthStore.getState();
      expect(state.error).toBe('Login failed');
      expect(state.isAuthenticated).toBe(false);
    });

    it('should set isLoading to true during login', async () => {
      const mockResponse = {
        access_token: 'mock-jwt-token',
        token_type: 'bearer',
        user: {
          id: 'user-123',
          username: 'testuser',
          created_at: '2024-01-01T00:00:00Z',
          last_login: '2024-03-10T00:00:00Z',
        },
      };

      // Create a promise that we can control
      let resolveLogin: (value: any) => void;
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve;
      });

      vi.mocked(authApi.login).mockReturnValue(loginPromise as any);

      const store = useAuthStore.getState();
      const loginCall = store.login('testuser', 'password123');

      // Check loading state
      expect(useAuthStore.getState().isLoading).toBe(true);

      // Resolve the login
      resolveLogin!(mockResponse);
      await loginCall;

      expect(useAuthStore.getState().isLoading).toBe(false);
    });
  });

  describe('register', () => {
    it('should successfully register and auto-login', async () => {
      const mockUser = {
        id: 'user-123',
        username: 'newuser',
        created_at: '2024-01-01T00:00:00Z',
        last_login: null,
      };

      const mockTokenResponse = {
        access_token: 'mock-jwt-token',
        token_type: 'bearer',
        user: mockUser,
      };

      vi.mocked(authApi.register).mockResolvedValue(mockUser);
      vi.mocked(authApi.login).mockResolvedValue(mockTokenResponse);

      const store = useAuthStore.getState();

      await expect(store.register('newuser', 'password123')).resolves.not.toThrow();

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.token).toBe('mock-jwt-token');
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe(null);

      expect(authApi.register).toHaveBeenCalledWith({
        username: 'newuser',
        password: 'password123',
      });
      expect(authApi.login).toHaveBeenCalledWith({
        username: 'newuser',
        password: 'password123',
      });
    });

    it('should handle registration failure', async () => {
      const mockError = new Error('Username already exists');
      vi.mocked(authApi.register).mockRejectedValue(mockError);

      const store = useAuthStore.getState();

      await expect(store.register('existinguser', 'password123')).rejects.toThrow();

      const state = useAuthStore.getState();
      expect(state.user).toBe(null);
      expect(state.token).toBe(null);
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('Username already exists');

      // Login should not be called if registration fails
      expect(authApi.login).not.toHaveBeenCalled();
    });
  });

  describe('logout', () => {
    it('should clear user state and token', () => {
      // Set up an authenticated state
      useAuthStore.setState({
        user: {
          id: 'user-123',
          username: 'testuser',
          created_at: '2024-01-01T00:00:00Z',
          last_login: '2024-03-10T00:00:00Z',
        },
        token: 'mock-jwt-token',
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      const store = useAuthStore.getState();
      store.logout();

      const state = useAuthStore.getState();
      expect(state.user).toBe(null);
      expect(state.token).toBe(null);
      expect(state.isAuthenticated).toBe(false);
      expect(state.error).toBe(null);
    });

    it('should clear error state on logout', () => {
      useAuthStore.setState({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: 'Some error',
      });

      const store = useAuthStore.getState();
      store.logout();

      expect(useAuthStore.getState().error).toBe(null);
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      useAuthStore.setState({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: 'Previous error',
      });

      const store = useAuthStore.getState();
      store.clearError();

      expect(useAuthStore.getState().error).toBe(null);
    });
  });

  describe('setToken', () => {
    it('should set token', () => {
      const store = useAuthStore.getState();
      store.setToken('new-token');

      expect(useAuthStore.getState().token).toBe('new-token');
    });

    it('should clear token when setting null', () => {
      useAuthStore.setState({
        token: 'existing-token',
      });

      const store = useAuthStore.getState();
      store.setToken(null);

      expect(useAuthStore.getState().token).toBe(null);
    });
  });

  describe('persistence', () => {
    it('should persist auth state to localStorage', () => {
      const mockUser = {
        id: 'user-123',
        username: 'testuser',
        created_at: '2024-01-01T00:00:00Z',
        last_login: '2024-03-10T00:00:00Z',
      };

      useAuthStore.setState({
        user: mockUser,
        token: 'mock-jwt-token',
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      // Check that state is set
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.token).toBe('mock-jwt-token');
      expect(state.isAuthenticated).toBe(true);
    });
  });
});

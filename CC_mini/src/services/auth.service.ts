import { apiClient } from './api';
import {
  RegisterRequest,
  RegisterResponse,
  LoginResponse,
  UserResponse,
} from '@/types';
import { storage } from '@/utils/storage';
import { mockAuthService } from './mock-auth.service';

// Set to false to use real backend API
const USE_MOCK = false;

export const authService = {
  /**
   * Register a new user
   */
  register: async (data: RegisterRequest): Promise<RegisterResponse> => {
    if (USE_MOCK) {
      return mockAuthService.register(data);
    }
    
    try {
      const response = await apiClient.post<RegisterResponse>('/register', data);
      return response.data;
    } catch (error: any) {
      // If backend is not available, provide helpful error
      if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        throw new Error('Backend server is not running. Please start the backend or enable mock mode.');
      }
      throw error;
    }
  },

  /**
   * Login and receive JWT token
   * Note: Backend expects form-urlencoded with 'username' field (not 'email')
   */
  login: async (email: string, password: string): Promise<LoginResponse> => {
    if (USE_MOCK) {
      return mockAuthService.login(email, password);
    }

    try {
      const formData = new URLSearchParams();
      formData.append('username', email); // Backend expects 'username' but value is email
      formData.append('password', password);

      const response = await apiClient.post<LoginResponse>('/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      // Store token
      storage.setToken(response.data.access_token);
      storage.setUserEmail(email);

      return response.data;
    } catch (error: any) {
      // If backend is not available, provide helpful error
      if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        throw new Error('Backend server is not running. Please start the backend or enable mock mode.');
      }
      throw error;
    }
  },

  /**
   * Get current authenticated user
   */
  getCurrentUser: async (): Promise<UserResponse> => {
    if (USE_MOCK) {
      return mockAuthService.getCurrentUser();
    }

    try {
      const response = await apiClient.get<UserResponse>('/users/me');
      return response.data;
    } catch (error: any) {
      // If backend is not available, provide helpful error
      if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        throw new Error('Backend server is not running. Please start the backend or enable mock mode.');
      }
      throw error;
    }
  },

  /**
   * Logout user (clear local storage)
   */
  logout: (): void => {
    if (USE_MOCK) {
      mockAuthService.logout();
    } else {
      storage.clear();
    }
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: (): boolean => {
    if (USE_MOCK) {
      return mockAuthService.isAuthenticated();
    }
    return !!storage.getToken();
  },
};

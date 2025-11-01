/**
 * Mock Authentication Service for Testing Without Backend
 * This simulates backend responses so you can test the frontend
 */

import { RegisterRequest, RegisterResponse, LoginResponse, UserResponse } from '@/types';
import { storage } from '@/utils/storage';

// Simulate a database with localStorage
const USERS_KEY = 'mock_users';

interface MockUser {
  email: string;
  password: string;
  id: string;
  created_at: string;
}

const getMockUsers = (): MockUser[] => {
  const users = localStorage.getItem(USERS_KEY);
  return users ? JSON.parse(users) : [];
};

const saveMockUsers = (users: MockUser[]) => {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
};

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const mockAuthService = {
  /**
   * Mock Register
   */
  register: async (data: RegisterRequest): Promise<RegisterResponse> => {
    await delay(500); // Simulate network delay

    const users = getMockUsers();
    
    // Check if user exists
    if (users.find(u => u.email === data.email)) {
      throw new Error('User already exists');
    }

    // Create new user
    const newUser: MockUser = {
      email: data.email,
      password: data.password, // In real backend, this would be hashed
      id: Math.random().toString(36).substr(2, 9),
      created_at: new Date().toISOString(),
    };

    users.push(newUser);
    saveMockUsers(users);

    return {
      email: newUser.email,
      created_at: newUser.created_at,
    };
  },

  /**
   * Mock Login
   */
  login: async (email: string, password: string): Promise<LoginResponse> => {
    await delay(500); // Simulate network delay

    const users = getMockUsers();
    const user = users.find(u => u.email === email && u.password === password);

    if (!user) {
      throw new Error('Invalid credentials');
    }

    // Generate mock JWT token
    const mockToken = `mock_jwt_${user.id}_${Date.now()}`;

    // Store token
    storage.setToken(mockToken);
    storage.setUserEmail(email);

    return {
      access_token: mockToken,
      token_type: 'bearer',
    };
  },

  /**
   * Mock Get Current User
   */
  getCurrentUser: async (): Promise<UserResponse> => {
    await delay(300); // Simulate network delay

    const email = storage.getUserEmail();
    if (!email) {
      throw new Error('Not authenticated');
    }

    const users = getMockUsers();
    const user = users.find(u => u.email === email);

    if (!user) {
      throw new Error('User not found');
    }

    return {
      email: user.email,
      created_at: user.created_at,
    };
  },

  /**
   * Mock Logout
   */
  logout: (): void => {
    storage.clear();
  },

  /**
   * Check if authenticated
   */
  isAuthenticated: (): boolean => {
    return !!storage.getToken();
  },

  /**
   * Clear all mock users (for testing)
   */
  clearAllUsers: (): void => {
    localStorage.removeItem(USERS_KEY);
  },
};

import { STORAGE_KEYS } from '@/config/constants';

export const storage = {
  getToken: (): string | null => {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  },

  setToken: (token: string): void => {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token);
  },

  removeToken: (): void => {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
  },

  getUserEmail: (): string | null => {
    return localStorage.getItem(STORAGE_KEYS.USER_EMAIL);
  },

  setUserEmail: (email: string): void => {
    localStorage.setItem(STORAGE_KEYS.USER_EMAIL, email);
  },

  removeUserEmail: (): void => {
    localStorage.removeItem(STORAGE_KEYS.USER_EMAIL);
  },

  clear: (): void => {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER_EMAIL);
  },
};

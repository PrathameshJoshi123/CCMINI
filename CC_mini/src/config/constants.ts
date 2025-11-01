export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const POLLING_INTERVAL = Number(import.meta.env.VITE_POLLING_INTERVAL) || 5000;
export const MAX_FILE_SIZE = Number(import.meta.env.VITE_MAX_FILE_SIZE) || 52428800; // 50MB

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  USER_EMAIL: 'user_email',
} as const;

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  DOCUMENT_DETAIL: '/documents/:documentId',
  CHAT: '/chat',
} as const;

export const QUERY_KEYS = {
  DOCUMENTS: 'documents',
  DOCUMENT: 'document',
  GENERATED: 'generated',
  USER: 'user',
} as const;

export const PROCESSING_STATUS_COLORS = {
  UPLOADING: 'bg-blue-100 text-blue-800',
  PROCESSING: 'bg-yellow-100 text-yellow-800',
  COMPLETED: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
} as const;

export const PROCESSING_STATUS_LABELS = {
  UPLOADING: 'Uploading',
  PROCESSING: 'Processing',
  COMPLETED: 'Completed',
  FAILED: 'Failed',
} as const;

export const MAX_POLLING_DURATION = 120000; // 2 minutes

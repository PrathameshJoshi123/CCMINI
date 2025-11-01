import { apiClient } from './api';
import { Document, UploadResponse, GeneratedContent } from '@/types';
import { mockDocumentsService } from './mock-documents.service';

// Set to false to use real backend API
const USE_MOCK = false;

export const documentsService = {
  /**
   * Upload a PDF document
   */
  uploadDocument: async (
    file: File,
    onUploadProgress?: (progressEvent: { loaded: number; total?: number }) => void
  ): Promise<UploadResponse> => {
    if (USE_MOCK) {
      return mockDocumentsService.uploadDocument(file);
    }

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post<UploadResponse>('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress,
      });

      return response.data;
    } catch (error: any) {
      if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        throw new Error('Backend server is not running. Documents feature requires the backend.');
      }
      throw error;
    }
  },

  /**
   * Get all documents for authenticated user
   */
  getDocuments: async (): Promise<Document[]> => {
    if (USE_MOCK) {
      return mockDocumentsService.getDocuments();
    }

    try {
      const response = await apiClient.get<Document[]>('/documents');
      return response.data;
    } catch (error: any) {
      if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        throw new Error('Backend server is not running. Documents feature requires the backend.');
      }
      throw error;
    }
  },

  /**
   * Get a single document by ID
   */
  getDocument: async (documentId: string): Promise<Document> => {
    if (USE_MOCK) {
      return mockDocumentsService.getDocument(documentId);
    }

    try {
      const documents = await documentsService.getDocuments();
      const document = documents.find((doc) => doc._id === documentId);

      if (!document) {
        throw new Error('Document not found');
      }

      return document;
    } catch (error: any) {
      if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        throw new Error('Backend server is not running. Documents feature requires the backend.');
      }
      throw error;
    }
  },

  /**
   * Get generated content for a document
   */
  getGeneratedContent: async (documentId: string): Promise<GeneratedContent[]> => {
    if (USE_MOCK) {
      return mockDocumentsService.getGeneratedContent(documentId);
    }

    try {
      const response = await apiClient.get<GeneratedContent[]>(
        `/documents/${documentId}/generated`
      );
      return response.data;
    } catch (error: any) {
      if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        throw new Error('Backend server is not running. Documents feature requires the backend.');
      }
      throw error;
    }
  },
};

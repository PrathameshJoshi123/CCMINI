import { apiClient } from './api';
import { ChatRequest, ChatResponse } from '@/types';
import { mockChatService } from './mock-chat.service';

// Set to false to use real backend API
const USE_MOCK = false;

export const chatService = {
  /**
   * Send a chat query using RAG
   */
  sendMessage: async (query: string, documentIds: string[]): Promise<ChatResponse> => {
    if (USE_MOCK) {
      return mockChatService.sendMessage({ query, document_ids: documentIds });
    }

    try {
      const payload: ChatRequest = {
        query,
        document_ids: documentIds,
      };

      const response = await apiClient.post<ChatResponse>('/chat', payload);
      return response.data;
    } catch (error: any) {
      if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        throw new Error('Backend server is not running. Chat feature requires the backend.');
      }
      throw error;
    }
  },
};

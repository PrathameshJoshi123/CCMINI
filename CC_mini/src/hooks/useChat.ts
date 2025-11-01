import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { chatService } from '@/services/chat.service';
import { ChatMessage, ChatResponse } from '@/types';

export const useChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);

  const mutation = useMutation<ChatResponse, Error, string>({
    mutationFn: (query: string) => chatService.sendMessage(query, selectedDocuments),
    onMutate: (query) => {
      // Add user message optimistically
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: query,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
    },
    onSuccess: (response) => {
      // Add AI response
      const assistantMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    },
    onError: (error) => {
      // Add error message
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    },
  });

  const sendMessage = (query: string) => {
    if (!query.trim()) return;
    mutation.mutate(query);
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const toggleDocument = (documentId: string) => {
    setSelectedDocuments((prev) =>
      prev.includes(documentId)
        ? prev.filter((id) => id !== documentId)
        : [...prev, documentId]
    );
  };

  const selectAllDocuments = (documentIds: string[]) => {
    setSelectedDocuments(documentIds);
  };

  const clearSelectedDocuments = () => {
    setSelectedDocuments([]);
  };

  return {
    messages,
    selectedDocuments,
    sendMessage,
    clearMessages,
    toggleDocument,
    selectAllDocuments,
    clearSelectedDocuments,
    isLoading: mutation.isPending,
    error: mutation.error,
  };
};

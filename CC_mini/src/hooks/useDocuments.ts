import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsService } from '@/services/documents.service';
import { QUERY_KEYS } from '@/config/constants';
import { Document, GeneratedContent } from '@/types';

/**
 * Hook to fetch all documents
 */
export const useDocuments = () => {
  return useQuery<Document[], Error>({
    queryKey: [QUERY_KEYS.DOCUMENTS],
    queryFn: documentsService.getDocuments,
    refetchInterval: false,
  });
};

/**
 * Hook to fetch a single document
 */
export const useDocument = (documentId: string) => {
  return useQuery<Document, Error>({
    queryKey: [QUERY_KEYS.DOCUMENT, documentId],
    queryFn: () => documentsService.getDocument(documentId),
    enabled: !!documentId,
  });
};

/**
 * Hook to fetch generated content for a document
 */
export const useGeneratedContent = (documentId: string) => {
  return useQuery<GeneratedContent[], Error>({
    queryKey: [QUERY_KEYS.GENERATED, documentId],
    queryFn: () => documentsService.getGeneratedContent(documentId),
    enabled: !!documentId,
  });
};

/**
 * Hook to refetch documents manually
 */
export const useRefetchDocuments = () => {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.DOCUMENTS] });
  };
};

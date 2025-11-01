import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsService } from '@/services/documents.service';
import { QUERY_KEYS } from '@/config/constants';
import { UploadResponse } from '@/types';

interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export const useUpload = () => {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    loaded: 0,
    total: 0,
    percentage: 0,
  });
  const queryClient = useQueryClient();

  const mutation = useMutation<UploadResponse, Error, File>({
    mutationFn: (file: File) =>
      documentsService.uploadDocument(file, (progressEvent) => {
        const { loaded, total = 0 } = progressEvent;
        const percentage = total > 0 ? Math.round((loaded * 100) / total) : 0;
        setUploadProgress({ loaded, total, percentage });
      }),
    onSuccess: () => {
      // Invalidate documents query to refetch
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.DOCUMENTS] });
      // Reset progress
      setUploadProgress({ loaded: 0, total: 0, percentage: 0 });
    },
    onError: () => {
      // Reset progress on error
      setUploadProgress({ loaded: 0, total: 0, percentage: 0 });
    },
  });

  return {
    upload: mutation.mutate,
    uploadAsync: mutation.mutateAsync,
    isUploading: mutation.isPending,
    uploadProgress,
    error: mutation.error,
    reset: mutation.reset,
  };
};

import { useEffect, useRef, useCallback } from 'react';
import { POLLING_INTERVAL, MAX_POLLING_DURATION } from '@/config/constants';
import { ProcessingStatus } from '@/types';

interface PollingOptions {
  enabled: boolean;
  onComplete?: () => void;
  onFail?: () => void;
  onTimeout?: () => void;
}

/**
 * Hook to poll for document status changes
 */
export const usePolling = (
  status: ProcessingStatus | undefined,
  callback: () => void,
  options: PollingOptions = { enabled: true }
) => {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(Date.now());

  const cleanup = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!options.enabled || !status) {
      return;
    }

    // Start polling if status is UPLOADING or PROCESSING
    if (status === 'UPLOADING' || status === 'PROCESSING') {
      startTimeRef.current = Date.now();

      intervalRef.current = setInterval(() => {
        callback();
      }, POLLING_INTERVAL);

      // Stop polling after max duration
      timeoutRef.current = setTimeout(() => {
        cleanup();
        options.onTimeout?.();
      }, MAX_POLLING_DURATION);
    }

    // Stop polling if status is COMPLETED or FAILED
    if (status === 'COMPLETED') {
      cleanup();
      options.onComplete?.();
    } else if (status === 'FAILED') {
      cleanup();
      options.onFail?.();
    }

    return cleanup;
  }, [status, callback, options, cleanup]);

  return { cleanup };
};

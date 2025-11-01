import React from 'react';
import { ProcessingStatus } from '@/types';
import { PROCESSING_STATUS_COLORS, PROCESSING_STATUS_LABELS } from '@/config/constants';
import { Loader2, CheckCircle, XCircle, UploadCloud } from 'lucide-react';
import clsx from 'clsx';

interface StatusBadgeProps {
  status: ProcessingStatus;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getIcon = () => {
    switch (status) {
      case 'UPLOADING':
        return <UploadCloud className="h-4 w-4 mr-1" />;
      case 'PROCESSING':
        return <Loader2 className="h-4 w-4 mr-1 animate-spin" />;
      case 'COMPLETED':
        return <CheckCircle className="h-4 w-4 mr-1" />;
      case 'FAILED':
        return <XCircle className="h-4 w-4 mr-1" />;
    }
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        PROCESSING_STATUS_COLORS[status]
      )}
    >
      {getIcon()}
      {PROCESSING_STATUS_LABELS[status]}
    </span>
  );
};

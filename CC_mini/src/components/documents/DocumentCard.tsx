import React from 'react';
import { Link } from 'react-router-dom';
import { Document } from '@/types';
import { StatusBadge } from './StatusBadge';
import { formatRelativeTime } from '@/utils/format';
import { FileText, Eye } from 'lucide-react';

interface DocumentCardProps {
  document: Document;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({ document }) => {
  return (
    <Link
      to={`/documents/${document._id}`}
      className="block bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-200 p-4"
    >
      <div className="flex items-start space-x-3">
        <FileText className="h-10 w-10 text-primary-600 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-gray-900 truncate">
            {document.original_filename}
          </h3>
          <p className="text-xs text-gray-500 mt-1">
            {formatRelativeTime(document.uploaded_at)}
          </p>
          <div className="mt-2">
            <StatusBadge status={document.processing_status} />
          </div>
        </div>
        <Eye className="h-5 w-5 text-gray-400" />
      </div>
    </Link>
  );
};

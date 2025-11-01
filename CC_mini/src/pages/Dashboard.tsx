import React, { useState } from 'react';
import { Layout } from '@/components/layout/Layout';
import { FileUploader } from '@/components/documents/FileUploader';
import { DocumentCard } from '@/components/documents/DocumentCard';
import { useDocuments, useRefetchDocuments } from '@/hooks/useDocuments';
import { usePolling } from '@/hooks/usePolling';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Button } from '@/components/common/Button';
import { Plus, RefreshCw, FileText } from 'lucide-react';
import { Modal } from '@/components/common/Modal';

export const Dashboard: React.FC = () => {
  const { data: documents, isLoading, error } = useDocuments();
  const refetchDocuments = useRefetchDocuments();
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // Poll for documents with processing status
  const hasProcessingDocuments = documents?.some(
    (doc) => doc.processing_status === 'UPLOADING' || doc.processing_status === 'PROCESSING'
  );

  usePolling(hasProcessingDocuments ? 'PROCESSING' : 'COMPLETED', refetchDocuments, {
    enabled: hasProcessingDocuments || false,
  });

  if (isLoading) {
    return (
      <Layout>
        <LoadingSpinner size="lg" className="mt-20" />
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="text-center mt-20">
          <p className="text-red-600">Error loading documents: {error.message}</p>
          <Button onClick={refetchDocuments} className="mt-4">
            Retry
          </Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Documents</h1>
            <p className="text-sm text-gray-600 mt-1">
              {documents?.length || 0} document{documents?.length !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="flex space-x-2">
            <Button variant="secondary" onClick={refetchDocuments}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button onClick={() => setIsUploadModalOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Upload Document
            </Button>
          </div>
        </div>

        {/* Document Grid */}
        {documents && documents.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documents.map((doc) => (
              <DocumentCard key={doc._id} document={doc} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-300">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by uploading a PDF document.</p>
            <div className="mt-6">
              <Button onClick={() => setIsUploadModalOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Upload Your First Document
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        title="Upload Document"
        size="lg"
      >
        <FileUploader
          onUploadComplete={() => {
            setIsUploadModalOpen(false);
            refetchDocuments();
          }}
        />
      </Modal>
    </Layout>
  );
};

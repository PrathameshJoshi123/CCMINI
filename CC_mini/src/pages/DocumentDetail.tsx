import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { useDocument, useGeneratedContent } from '@/hooks/useDocuments';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { StatusBadge } from '@/components/documents/StatusBadge';
import { SummaryViewer } from '@/components/generated/SummaryViewer';
import { MindMapViewer } from '@/components/generated/MindMapViewer';
import { FlashcardViewer } from '@/components/generated/FlashcardViewer';
import { formatDate } from '@/utils/format';
import { FileText } from 'lucide-react';
import { SummaryData, MindMapData, FlashcardsData } from '@/types';

export const DocumentDetail: React.FC = () => {
  const { documentId } = useParams<{ documentId: string }>();
  const { data: document, isLoading: docLoading } = useDocument(documentId!);
  const { data: generatedContent, isLoading: contentLoading } = useGeneratedContent(documentId!);
  const [activeTab, setActiveTab] = useState<'summary' | 'mindmap' | 'flashcards'>('summary');

  if (docLoading || contentLoading) {
    return (
      <Layout>
        <LoadingSpinner size="lg" className="mt-20" />
      </Layout>
    );
  }

  if (!document) {
    return (
      <Layout>
        <div className="text-center mt-20">
          <p className="text-gray-600">Document not found</p>
        </div>
      </Layout>
    );
  }

  const summary = generatedContent?.find((c) => c.content_type === 'SUMMARY');
  const mindmap = generatedContent?.find((c) => c.content_type === 'MINDMAP');
  const flashcards = generatedContent?.find((c) => c.content_type === 'FLASHCARDS');

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-start space-x-4">
            <FileText className="h-10 w-10 text-primary-600 flex-shrink-0" />
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">{document.original_filename}</h1>
              <p className="text-sm text-gray-500 mt-1">Uploaded {formatDate(document.uploaded_at)}</p>
              <div className="mt-2">
                <StatusBadge status={document.processing_status} />
              </div>
            </div>
          </div>
        </div>

        {/* Generated Content */}
        {document.processing_status === 'COMPLETED' && generatedContent && generatedContent.length > 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            {/* Tabs */}
            <div className="border-b border-gray-200">
              <nav className="flex space-x-8 px-6" aria-label="Tabs">
                <button
                  onClick={() => setActiveTab('summary')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'summary'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Summary
                </button>
                <button
                  onClick={() => setActiveTab('mindmap')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'mindmap'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Mind Map
                </button>
                <button
                  onClick={() => setActiveTab('flashcards')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'flashcards'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Flashcards
                </button>
              </nav>
            </div>

            {/* Tab Content */}
            <div className="p-6">
              {activeTab === 'summary' && summary && (
                <SummaryViewer data={summary.content_data as SummaryData} />
              )}
              {activeTab === 'mindmap' && mindmap && (
                <MindMapViewer data={mindmap.content_data as MindMapData} />
              )}
              {activeTab === 'flashcards' && flashcards && (
                <FlashcardViewer data={flashcards.content_data as FlashcardsData} />
              )}
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <p className="text-gray-600">
              {document.processing_status === 'PROCESSING'
                ? 'Document is being processed. Generated content will appear here soon.'
                : document.processing_status === 'FAILED'
                ? 'Document processing failed. Please try uploading again.'
                : 'No generated content available yet.'}
            </p>
          </div>
        )}
      </div>
    </Layout>
  );
};

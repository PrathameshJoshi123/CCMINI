import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Layout } from '@/components/layout/Layout';
import { useChat } from '@/hooks/useChat';
import { useDocuments } from '@/hooks/useDocuments';
import { Button } from '@/components/common/Button';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Send, FileText, X } from 'lucide-react';
import { formatRelativeTime } from '@/utils/format';

export const Chat: React.FC = () => {
  const {
    messages,
    selectedDocuments,
    sendMessage,
    clearMessages,
    toggleDocument,
    selectAllDocuments,
    clearSelectedDocuments,
    isLoading,
  } = useChat();

  const { data: documents } = useDocuments();
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    sendMessage(inputValue);
    setInputValue('');
  };

  const completedDocs =
    documents?.filter((doc: any) => doc.processing_status === 'COMPLETED') || [];

  return (
    <Layout>
      <div className="h-[calc(100vh-12rem)] flex flex-col bg-white rounded-lg shadow-sm border border-gray-200">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h1 className="text-xl font-bold text-gray-900">Chat with Documents</h1>
            {messages.length > 0 && (
              <Button variant="secondary" size="sm" onClick={clearMessages}>
                Clear Chat
              </Button>
            )}
          </div>

          {/* Document Selector */}
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">Select Documents</label>
              <div className="space-x-2">
                <button
                  onClick={() => selectAllDocuments(completedDocs.map((d: any) => d._id))}
                  className="text-xs text-primary-600 hover:text-primary-700"
                >
                  Select All
                </button>
                <button
                  onClick={clearSelectedDocuments}
                  className="text-xs text-gray-600 hover:text-gray-700"
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {completedDocs.length === 0 ? (
                <p className="text-sm text-gray-500">No completed documents available</p>
              ) : (
                completedDocs.map((doc: any) => (
                  <button
                    key={doc._id}
                    onClick={() => toggleDocument(doc._id)}
                    className={`inline-flex items-center px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                      selectedDocuments.includes(doc._id)
                        ? 'bg-primary-100 text-primary-700 border border-primary-300'
                        : 'bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200'
                    }`}
                  >
                    <FileText className="h-4 w-4 mr-1" />
                    {doc.original_filename}
                    {selectedDocuments.includes(doc._id) && <X className="h-4 w-4 ml-1" />}
                  </button>
                ))
              )}
            </div>
            {selectedDocuments.length === 0 && completedDocs.length > 0 && (
              <p className="text-xs text-gray-500 mt-2">
                No documents selected. Messages will search across all documents.
              </p>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center mt-20">
              <p className="text-gray-500">Ask a question about your documents</p>
              <p className="text-sm text-gray-400 mt-2">
                Example: "What are the main topics covered?"
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <div
                    className={`prose prose-sm md:prose-base max-w-none ${
                      message.role === 'user'
                        ? 'prose-invert prose-headings:text-white prose-strong:text-white prose-code:text-white prose-pre:bg-gray-800'
                        : 'prose-headings:text-gray-900 prose-strong:text-gray-900 prose-code:bg-gray-200 prose-code:text-gray-800 prose-pre:bg-gray-50'
                    } prose-table:text-sm prose-th:p-2 prose-td:p-2 prose-th:border prose-td:border prose-table:border-collapse`}
                  >
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw]}
                      components={{
                        table: ({ children }) => (
                          <div className="overflow-x-auto my-4">
                            <table className="min-w-full border-collapse border border-gray-300">
                              {children}
                            </table>
                          </div>
                        ),
                        th: ({ children }) => (
                          <th className="border border-gray-300 bg-gray-50 px-3 py-2 text-left font-semibold">
                            {children}
                          </th>
                        ),
                        td: ({ children }) => (
                          <td className="border border-gray-300 px-3 py-2">{children}</td>
                        ),
                        code: ({ children, className }) => {
                          const isInline = !className;
                          return isInline ? (
                            <code className="bg-gray-200 text-gray-800 px-1 py-0.5 rounded text-sm font-mono">
                              {children}
                            </code>
                          ) : (
                            <code className={className}>{children}</code>
                          );
                        },
                        pre: ({ children }) => (
                          <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                            {children}
                          </pre>
                        ),
                        h1: ({ children }) => (
                          <h1 className="text-2xl font-bold mb-4 mt-6 pb-2 border-b border-gray-200">
                            {children}
                          </h1>
                        ),
                        h2: ({ children }) => (
                          <h2 className="text-xl font-bold mb-3 mt-5">{children}</h2>
                        ),
                        h3: ({ children }) => (
                          <h3 className="text-lg font-semibold mb-2 mt-4">{children}</h3>
                        ),
                        ul: ({ children }) => (
                          <ul className="list-disc list-inside space-y-1 my-3">{children}</ul>
                        ),
                        ol: ({ children }) => (
                          <ol className="list-decimal list-inside space-y-1 my-3">{children}</ol>
                        ),
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-4 border-blue-500 pl-4 py-2 my-4 bg-blue-50 text-blue-800 italic">
                            {children}
                          </blockquote>
                        ),
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>

                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-300">
                      <p className="text-xs font-medium mb-2">Sources:</p>
                      <div className="space-y-1">
                        {message.sources.map((source, idx) => {
                          const doc = documents?.find((d: any) => d._id === source.document_id);
                          return (
                            <div key={idx} className="text-xs">
                              <span className="font-medium">{doc?.original_filename}</span>
                              {' - Page '}
                              {source.page}
                              {source.score && ` (${Math.round(source.score * 100)}% relevant)`}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  <p className="text-xs opacity-75 mt-2">
                    {formatRelativeTime(message.timestamp.toISOString())}
                  </p>
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg p-4">
                <LoadingSpinner size="sm" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
          <div className="flex space-x-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask a question..."
              disabled={isLoading || completedDocs.length === 0}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <Button
              type="submit"
              disabled={isLoading || !inputValue.trim() || completedDocs.length === 0}
            >
              <Send className="h-5 w-5" />
            </Button>
          </div>
          {completedDocs.length === 0 && (
            <p className="text-xs text-gray-500 mt-2">
              Upload and process documents before chatting
            </p>
          )}
        </form>
      </div>
    </Layout>
  );
};

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { SummaryData } from '@/types';
import { Copy, Download } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { toast } from 'sonner';

interface SummaryViewerProps {
  data: SummaryData;
}

export const SummaryViewer: React.FC<SummaryViewerProps> = ({ data }) => {
  const handleCopy = () => {
    navigator.clipboard.writeText(data.summary);
    toast.success('Summary copied to clipboard!');
  };

  const handleDownload = () => {
    const blob = new Blob([data.summary], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'summary.txt';
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Summary downloaded!');
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end space-x-2">
        <Button variant="secondary" size="sm" onClick={handleCopy}>
          <Copy className="h-4 w-4 mr-2" />
          Copy
        </Button>
        <Button variant="secondary" size="sm" onClick={handleDownload}>
          <Download className="h-4 w-4 mr-2" />
          Download
        </Button>
      </div>
      <div className="prose prose-lg max-w-none bg-gray-50 rounded-lg p-6">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{data.summary}</ReactMarkdown>
      </div>
    </div>
  );
};

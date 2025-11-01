import { useState } from 'react';
import { AlertCircle, X } from 'lucide-react';

export const MockModeBanner: React.FC = () => {
  const [isVisible, setIsVisible] = useState(true);
  const isMockMode = import.meta.env.VITE_USE_MOCK_AUTH === 'true';

  if (!isMockMode || !isVisible) return null;

  return (
    <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0" />
          <p className="text-sm text-yellow-800">
            <strong>Demo Mode:</strong> Using simulated data - no backend needed! Try uploading documents, viewing AI content, and chatting. 
            <span className="hidden sm:inline"> All features work with sample data.</span>
          </p>
        </div>
        <button
          onClick={() => setIsVisible(false)}
          className="text-yellow-600 hover:text-yellow-800 transition-colors flex-shrink-0"
          aria-label="Close banner"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
};

import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { useUpload } from '@/hooks/useUpload';
import { validateFile } from '@/utils/validation';
import { MAX_FILE_SIZE } from '@/config/constants';
import { toast } from 'sonner';

interface FileUploaderProps {
  onUploadComplete?: (documentId: string) => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onUploadComplete }) => {
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const { upload, isUploading, uploadProgress } = useUpload();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    const error = validateFile(file, MAX_FILE_SIZE);
    if (error) {
      toast.error(error);
      return;
    }

    setSelectedFile(file);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: false,
    disabled: isUploading,
  });

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      upload(selectedFile, {
        onSuccess: (data) => {
          toast.success('File uploaded successfully!');
          setSelectedFile(null);
          onUploadComplete?.(data.document_id);
        },
        onError: (error: any) => {
          toast.error(error.response?.data?.detail || 'Upload failed');
        },
      });
    } catch (error) {
      console.error('Upload error:', error);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
  };

  return (
    <div className="space-y-4">
      {!selectedFile ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400'
          } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600">
            {isDragActive ? 'Drop the PDF file here' : 'Drag & drop a PDF file here, or click to select'}
          </p>
          <p className="mt-1 text-xs text-gray-500">PDF files up to 50MB</p>
        </div>
      ) : (
        <div className="border border-gray-300 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="h-8 w-8 text-primary-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
            </div>
            {!isUploading && (
              <button onClick={clearFile} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            )}
          </div>

          {isUploading && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Uploading...</span>
                <span>{uploadProgress.percentage}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress.percentage}%` }}
                />
              </div>
            </div>
          )}

          {!isUploading && (
            <div className="mt-4">
              <Button onClick={handleUpload} className="w-full">
                Upload Document
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

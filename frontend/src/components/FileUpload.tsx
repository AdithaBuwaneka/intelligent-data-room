/**
 * FileUpload Component
 *
 * Drag-and-drop file upload for CSV/XLSX files.
 * Validates file type and size (max 10MB).
 */

import { useCallback, useState } from 'react';
import type { FileMetadata } from '../types';
import { LoadingSpinner } from './LoadingSpinner';

interface FileUploadProps {
  onFileUploaded: (metadata: FileMetadata) => void;
  sessionId: string;
  isUploading: boolean;
  onUploadStart: () => void;
  onUploadEnd: () => void;
  onError: (error: string) => void;
  initialFile?: FileMetadata | null;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls'];

export function FileUpload({
  onFileUploaded,
  sessionId,
  isUploading,
  onUploadStart,
  onUploadEnd,
  onError,
  initialFile = null,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<FileMetadata | null>(initialFile);

  const validateFile = (file: File): string | null => {
    // Check file extension
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      return 'Invalid file type. Please upload a CSV or XLSX file.';
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return 'File too large. Maximum size is 10MB.';
    }

    return null;
  };

  const uploadFile = async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      onError(validationError);
      return;
    }

    onUploadStart();

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);

      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();

      const metadata: FileMetadata = {
        fileId: data.file_id,
        fileUrl: data.file_url,
        filename: data.filename,
        columns: data.columns,
        rowCount: data.row_count,
      };

      setUploadedFile(metadata);
      onFileUploaded(metadata);
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      onUploadEnd();
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const file = e.dataTransfer.files[0];
      if (file) {
        uploadFile(file);
      }
    },
    [sessionId]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        uploadFile(file);
      }
    },
    [sessionId]
  );

  const handleRemoveFile = () => {
    setUploadedFile(null);
  };

  // Show uploaded file info
  if (uploadedFile) {
    return (
      <div className="card p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Uploaded Data</h2>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg
                className="w-5 h-5 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-900 truncate">
                {uploadedFile.filename}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {uploadedFile.rowCount.toLocaleString()} rows &bull;{' '}
                {uploadedFile.columns.length} columns
              </p>
            </div>
            <button
              onClick={handleRemoveFile}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              title="Remove file"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Column preview */}
          <div className="mt-4">
            <p className="text-xs font-medium text-gray-500 uppercase mb-2">Columns</p>
            <div className="flex flex-wrap gap-1.5">
              {uploadedFile.columns.slice(0, 8).map((col) => (
                <span
                  key={col}
                  className="px-2 py-1 bg-white text-xs text-gray-700 rounded border border-gray-200"
                >
                  {col}
                </span>
              ))}
              {uploadedFile.columns.length > 8 && (
                <span className="px-2 py-1 text-xs text-gray-500">
                  +{uploadedFile.columns.length - 8} more
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show upload area
  return (
    <div className="card p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4">Upload Data</h2>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-all cursor-pointer
          ${isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
          }
          ${isUploading ? 'pointer-events-none opacity-60' : ''}
        `}
      >
        {isUploading ? (
          <LoadingSpinner size="lg" text="Uploading file..." />
        ) : (
          <>
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p className="mt-2 text-sm text-gray-600">
                <span className="text-blue-600 font-medium">Click to upload</span> or
                drag and drop
              </p>
              <p className="mt-1 text-xs text-gray-400">CSV or XLSX (max 10MB)</p>
            </label>
          </>
        )}
      </div>
    </div>
  );
}

export default FileUpload;

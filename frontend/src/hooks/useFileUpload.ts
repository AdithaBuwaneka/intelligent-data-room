/**
 * useFileUpload Hook
 *
 * Manages file upload state and operations.
 */

import { useState, useCallback } from 'react';
import type { FileMetadata } from '../types';

interface UseFileUploadReturn {
  file: FileMetadata | null;
  isUploading: boolean;
  error: string | null;
  setFile: (metadata: FileMetadata | null) => void;
  setIsUploading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearFile: () => void;
}

export function useFileUpload(): UseFileUploadReturn {
  const [file, setFile] = useState<FileMetadata | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearFile = useCallback(() => {
    setFile(null);
    setError(null);
  }, []);

  return {
    file,
    isUploading,
    error,
    setFile,
    setIsUploading,
    setError,
    clearFile,
  };
}

export default useFileUpload;

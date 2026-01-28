/**
 * useFileUpload Hook
 *
 * Manages file upload state and operations.
 * Persists file metadata to localStorage for session restoration after refresh.
 */

import { useState, useCallback, useEffect } from 'react';
import type { FileMetadata } from '../types';

const FILE_STORAGE_KEY = 'idr_uploaded_file';

interface UseFileUploadReturn {
  file: FileMetadata | null;
  isUploading: boolean;
  error: string | null;
  isRestoring: boolean;
  setFile: (metadata: FileMetadata | null) => void;
  setIsUploading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearFile: () => void;
  restoreFile: (sessionId: string) => Promise<void>;
}

export function useFileUpload(): UseFileUploadReturn {
  const [file, setFileState] = useState<FileMetadata | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRestoring, setIsRestoring] = useState(false);

  // Wrapper to persist file to localStorage
  const setFile = useCallback((metadata: FileMetadata | null) => {
    setFileState(metadata);
    if (metadata) {
      localStorage.setItem(FILE_STORAGE_KEY, JSON.stringify(metadata));
    } else {
      localStorage.removeItem(FILE_STORAGE_KEY);
    }
  }, []);

  // Restore file from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(FILE_STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as FileMetadata;
        setFileState(parsed);
      } catch {
        localStorage.removeItem(FILE_STORAGE_KEY);
      }
    }
  }, []);

  // Restore file from backend API (fallback if localStorage is empty)
  const restoreFile = useCallback(async (sessionId: string) => {
    // Skip if already have a file
    if (file) return;

    setIsRestoring(true);
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/session/${sessionId}/file`);

      if (response.ok) {
        const data = await response.json();
        const restoredFile: FileMetadata = {
          fileId: data.file_id,
          fileUrl: data.file_url,
          filename: data.filename,
          columns: data.columns,
          rowCount: data.row_count,
        };
        setFile(restoredFile);
      }
      // If 404, no file exists for this session - that's okay
    } catch (err) {
      console.warn('Failed to restore file from session:', err);
    } finally {
      setIsRestoring(false);
    }
  }, [file, setFile]);

  const clearFile = useCallback(() => {
    setFile(null);
    setError(null);
  }, [setFile]);

  return {
    file,
    isUploading,
    error,
    isRestoring,
    setFile,
    setIsUploading,
    setError,
    clearFile,
    restoreFile,
  };
}

export default useFileUpload;


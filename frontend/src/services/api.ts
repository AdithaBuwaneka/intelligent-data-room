import { FileUploadResponse, QueryRequest, QueryResponse, Message } from '../types';

// API base URL - will be set from environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Custom error class for API errors
 */
class ApiError extends Error {
  constructor(public statusCode: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        response.status,
        errorData.detail || `HTTP error! status: ${response.status}`
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(500, 'Network error. Please check your connection.');
  }
}

/**
 * Upload a CSV/XLSX file to the backend
 * @param file - The file to upload
 * @param sessionId - Current session ID
 * @returns File metadata including URL and columns
 */
export async function uploadFile(
  file: File,
  sessionId: string
): Promise<FileUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);

  return fetchApi<FileUploadResponse>('/api/upload', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Send a query to the multi-agent system
 * @param request - Query request with session_id, question, and file_url
 * @returns Answer, plan, and optional chart configuration
 */
export async function sendQuery(request: QueryRequest): Promise<QueryResponse> {
  return fetchApi<QueryResponse>('/api/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
}

/**
 * Get chat history for a session
 * @param sessionId - Session ID to fetch history for
 * @returns Array of messages
 */
export async function getChatHistory(sessionId: string): Promise<Message[]> {
  return fetchApi<Message[]>(`/api/history/${sessionId}`);
}

/**
 * Health check endpoint
 * @returns Health status
 */
export async function healthCheck(): Promise<{ status: string }> {
  return fetchApi<{ status: string }>('/health');
}

/**
 * Generate a unique session ID
 * @returns UUID string
 */
export function generateSessionId(): string {
  return crypto.randomUUID();
}
